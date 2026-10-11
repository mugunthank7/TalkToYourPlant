"""Build training and test telemetry with the existing sensor generator.

Healthy shifts: micro-stops on, no faults. Faulty shifts: bearing-style wear on a random machine with random
severity, repaired in time, late, or never. Seeds are split so that test episodes are never seen in training.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "data"))
from plantdata import events as ev  # noqa: E402
from plantdata import sensors  # noqa: E402

SHIFT = 8 * 3600
CLOCK = {"A": 6 * 3600, "B": 14 * 3600}


def aggregate(df: pd.DataFrame, shift_id: str, clock_start: int) -> pd.DataFrame:
    d = df.assign(minute=df["t_s"] // 60, up=(~df["state"].isin(["stopped", "maintenance", "failed"])).astype(float))
    g = d.groupby(["minute", "machine_id"], sort=True).agg(
        vib_mean=("vibration_rms_mm_s", "mean"), band_mean=("vib_bpfo_band", "mean"), temp_mean=("temperature_c", "mean"),
        cur_mean=("motor_current_a", "mean"), load_mean=("load_pct", "mean"), up_frac=("up", "mean"),
        fault_label=("fault_label", "max"), degradation=("degradation", "mean"), rul_s=("rul_s", "min")).reset_index()
    g["clock_s"] = clock_start + g["minute"] * 60
    g["shift_id"] = shift_id
    return g


def healthy_shift(seed: int, shift: str = "A") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df, _ = sensors.generate(SHIFT, rng, [], micro_stops=True, clock_start_s=CLOCK[shift])
    return aggregate(df, f"H{seed}", CLOCK[shift])


def faulty_shift(seed: int, machine: str | None = None, shift: str = "A", nominal: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mid = machine or str(rng.choice(list(sensors.PROFILE)))
    onset = float(rng.uniform(0.4, 3.6) * 3600)
    ramp = float(rng.uniform(2.0, 3.6) * 3600)
    over = {}
    if not nominal:
        over = dict(vib_gain=float(rng.uniform(1.8, 3.4)), band_gain=float(rng.uniform(8, 20)),
                    temp_rise_c=float(rng.uniform(7, 18)), current_gain=float(rng.uniform(0.06, 0.16)))
    f0 = sensors.make_fault(mid, f"{mid.lower()}_main_bearing", onset, ramp, None, 0.0, **over)
    fail = onset + ramp
    alert = ev.alert_time(f0)
    outcome = str(rng.choice(["timely", "late", "failure"], p=[0.5, 0.25, 0.25]))
    rs = None if outcome == "failure" else (alert + rng.uniform(5, 15) * 60 if outcome == "timely" else alert + 0.7 * (fail - alert))
    re = (rs + 1500) if rs is not None else fail + 5400
    f0.update(repair_start_s=rs, repair_end_s=float(re))
    df, _ = sensors.generate(SHIFT, rng, [f0], micro_stops=True, clock_start_s=CLOCK[shift])
    out = aggregate(df, f"F{seed}-{mid}", CLOCK[shift])
    out["fault_machine"] = mid
    out["onset_s"], out["fail_s"], out["rule_alert_s"], out["outcome"] = onset, fail, alert, outcome
    out["repair_start_s"] = rs if rs is not None else np.nan
    return out


def build(n_healthy: int, n_faulty: int, seed0: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    h = pd.concat([healthy_shift(seed0 + i, "A" if i % 2 == 0 else "B") for i in range(n_healthy)], ignore_index=True)
    f = pd.concat([faulty_shift(seed0 + 1000 + i, shift="A" if i % 2 == 0 else "B") for i in range(n_faulty)], ignore_index=True)
    return h, f


if __name__ == "__main__":
    out = ROOT / "sim" / "models" / "data"
    out.mkdir(parents=True, exist_ok=True)
    tr_h, tr_f = build(40, 70, 100)           # training pool (healthy used for fitting; faulty used for RUL)
    te_h, te_f = build(16, 40, 9000)          # held-out test: different seeds
    for name, d in (("train_healthy", tr_h), ("train_faulty", tr_f), ("test_healthy", te_h), ("test_faulty", te_f)):
        d.to_parquet(out / f"{name}.parquet", compression="zstd", index=False)
        print(name, d.shape)
