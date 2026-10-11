"""Turn 1-minute machine telemetry into load-normalised health features.

The sensors depend on how hard the machine is working, so each signal is divided by what a healthy machine
of that kind produces at the same load (learned from healthy data only). A ratio of 1.0 means "as healthy".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

FEATURES = ["vib_ratio", "band_ratio", "temp_resid", "cur_ratio", "vib_slope", "band_slope"]
LABELS = {"vib_ratio": "vibration", "band_ratio": "bearing-defect band", "temp_resid": "temperature",
          "cur_ratio": "motor current", "vib_slope": "vibration trend", "band_slope": "bearing-band trend"}
MIN_LOAD = 20.0          # percent: below this the machine is idle and ratios are meaningless
MIN_UP = 0.9             # share of the minute the machine was running


ALPHA_MIN = 1 - (1 - 1 / 900) ** 60   # per-minute step of the 900 s thermal lag


def lag_load(load: np.ndarray) -> np.ndarray:
    """Thermal state: first-order lag (900 s) of the load, so temperature is compared with what the machine's recent
    load predicts, not its instantaneous load. Starts at the first value."""
    out = np.empty(len(load))
    z = float(load[0]) if len(load) else 0.0
    for i, v in enumerate(load):
        z += ALPHA_MIN * (float(v) - z)
        out[i] = z
    return out


def ambient(t_s: np.ndarray | float) -> np.ndarray | float:
    return 24 + 3 * np.sin(2 * np.pi * (np.asarray(t_s) / 86400 - 0.3))


@dataclass
class Baseline:
    """y = a + b * load (load 0..1) per signal, for one machine. Fitted on healthy running minutes."""
    coef: dict = field(default_factory=dict)     # signal -> (a, b)
    noise: dict = field(default_factory=dict)    # signal -> residual std (for z-scores in reports)

    def expected(self, sig: str, load: np.ndarray) -> np.ndarray:
        a, b = self.coef[sig]
        return a + b * load


def running_mask(df: pd.DataFrame) -> np.ndarray:
    return ((df["load_mean"] >= MIN_LOAD) & (df["up_frac"] >= MIN_UP)).to_numpy()


def fit_baseline(df: pd.DataFrame, rise: float | None = None) -> Baseline:
    """df: healthy minutes of ONE machine with columns vib_mean, band_mean, temp_mean, cur_mean, load_mean, up_frac, clock_s."""
    df = df.sort_values("minute").reset_index(drop=True)
    m = running_mask(df)
    lagged = lag_load(df["load_mean"].to_numpy() / 100.0)[m]
    d = df[m]
    load = d["load_mean"].to_numpy() / 100.0
    bl = Baseline()
    amb = ambient(d["clock_s"].to_numpy())
    for sig, col in (("vib", "vib_mean"), ("band", "band_mean"), ("cur", "cur_mean"), ("temp", "temp_mean")):
        y = d[col].to_numpy() - (amb if sig == "temp" else 0.0)
        x = lagged if sig == "temp" else load
        A = np.vstack([np.ones_like(x), x]).T
        if sig == "temp" and rise is not None:      # rated temperature rise at full load is a design value; fit only the offset
            coef = np.array([float(np.mean(y - rise * x)), float(rise)])
        else:
            coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        bl.coef[sig] = (float(coef[0]), float(coef[1]))
        bl.noise[sig] = float(np.std(y - A @ coef))
    return bl


def minute_features(df: pd.DataFrame, bl: Baseline, win: int = 5, slope_min: int = 30) -> pd.DataFrame:
    """Features per minute for one machine (rows sorted by minute). Rows where the machine is not running are NaN."""
    df = df.sort_values("minute").reset_index(drop=True)
    ok = running_mask(df)
    load = df["load_mean"].to_numpy() / 100.0
    amb = ambient(df["clock_s"].to_numpy())
    r = pd.DataFrame(index=df.index)
    r["vib_ratio"] = df["vib_mean"] / bl.expected("vib", load)
    r["band_ratio"] = df["band_mean"] / np.maximum(bl.expected("band", load), 1e-6)
    r["cur_ratio"] = df["cur_mean"] / bl.expected("cur", load)
    r["temp_resid"] = df["temp_mean"] - amb - bl.expected("temp", lag_load(load))
    r.loc[~ok, :] = np.nan
    sm = r.rolling(win, min_periods=3).mean()
    out = pd.DataFrame({"minute": df["minute"], "vib_ratio": sm["vib_ratio"], "band_ratio": sm["band_ratio"],
                        "temp_resid": sm["temp_resid"], "cur_ratio": sm["cur_ratio"]})
    # slopes: change of the smoothed ratio over the last slope_min minutes, per hour
    for k in ("vib", "band"):
        s = sm[f"{k}_ratio"]
        past = s.shift(slope_min).rolling(win, min_periods=2).mean()
        out[f"{k}_slope"] = (s - past) / (slope_min / 60.0)
    # for the first slope_min minutes there is no past: treat as flat
    out[["vib_slope", "band_slope"]] = out[["vib_slope", "band_slope"]].fillna(0.0).where(sm["vib_ratio"].notna(), np.nan)
    return out
