"""Runtime anomaly monitor: streams 1-minute machine telemetry, scores it, raises watch/critical alerts with
Shapley explanations and a remaining-useful-life estimate. Pure Python per minute, so it is cheap enough to run
for every machine inside the simulation.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from .fastiso import FastIso
from .features import ALPHA_MIN, FEATURES, LABELS, MIN_LOAD, MIN_UP, ambient
from .shapley import shapley

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "anomaly.joblib"
WIN, SLOPE_MIN = 5, 30


@lru_cache(maxsize=1)
def load_model() -> dict:
    return joblib.load(MODEL_PATH)


def score_fn(model: dict):
    """Anomaly score, higher = more anomalous (identical to -IsolationForest.score_samples, but fast)."""
    if "_fast" not in model:
        model["_fast"] = FastIso(model["iso"])
    return model["_fast"].score


def _mean(xs) -> float:
    xs = [x for x in xs if x == x]
    return sum(xs) / len(xs) if len(xs) >= 3 else float("nan")


@dataclass
class MachineState:
    ratios: deque = field(default_factory=lambda: deque(maxlen=WIN))           # raw per-minute (vib, band, temp, cur) ratios
    smooth: deque = field(default_factory=lambda: deque(maxlen=SLOPE_MIN + WIN + 2))   # smoothed (vib, band)
    above_w: int = 0
    above_c: int = 0
    below: int = 0
    watch_t: float | None = None
    critical_t: float | None = None
    last: dict = field(default_factory=dict)
    lag: float | None = None                                                   # thermal state (lagged load)


class Monitor:
    """One instance per plant. Call `push(machine, minute_stats, t)` once per machine per simulated minute."""

    def __init__(self) -> None:
        self.m = load_model()
        self.sf = score_fn(self.m)
        self.state: dict[str, MachineState] = {}
        self.events: list[dict] = []
        self.history: dict[str, deque] = {}

    # -- features ------------------------------------------------------------------------------------
    def _features(self, st: MachineState, mid: str, row: dict) -> np.ndarray | None:
        bl = self.m["baselines"].get(mid)
        if bl is None:
            return None
        ok = row["load_mean"] >= MIN_LOAD and row["up_frac"] >= MIN_UP
        ld = row["load_mean"] / 100.0
        st.lag = ld if st.lag is None else st.lag
        st.lag += ALPHA_MIN * (ld - st.lag)
        if not ok:
            st.ratios.append((float("nan"),) * 4)
            st.smooth.append((float("nan"), float("nan")))
            return None
        load = row["load_mean"] / 100.0
        e = {k: bl.coef[k][0] + bl.coef[k][1] * (st.lag if k == "temp" else load) for k in ("vib", "band", "cur", "temp")}
        amb = float(ambient(row["clock_s"]))
        r = (row["vib_mean"] / e["vib"], row["band_mean"] / max(e["band"], 1e-6), row["temp_mean"] - amb - e["temp"], row["cur_mean"] / e["cur"])
        st.ratios.append(r)
        sm = tuple(_mean([x[i] for x in st.ratios]) for i in range(4))
        st.smooth.append((sm[0], sm[1]))
        if any(v != v for v in sm) or len(st.smooth) < 6:
            return None
        past = list(st.smooth)
        if len(past) > SLOPE_MIN:
            p5 = [q for q in past[max(0, len(past) - SLOPE_MIN - WIN):len(past) - SLOPE_MIN] if q[0] == q[0]]
            if len(p5) >= 2:
                pv, pb = sum(q[0] for q in p5) / len(p5), sum(q[1] for q in p5) / len(p5)
            else:
                pv, pb = sm[0], sm[1]
            vs, bs = (sm[0] - pv) / (SLOPE_MIN / 60), (sm[1] - pb) / (SLOPE_MIN / 60)
        else:
            vs = bs = 0.0
        return np.array([sm[0], sm[1], sm[2], sm[3], vs, bs])

    # -- streaming -----------------------------------------------------------------------------------
    def push(self, mid: str, row: dict, t: float) -> list[dict]:
        st = self.state.setdefault(mid, MachineState())
        x = self._features(st, mid, row)
        out: list[dict] = []
        if x is None:
            return out
        score = float(self.sf(x[None, :])[0])
        st.last = {"t": round(t, 1), "score": round(score, 4), "features": dict(zip(FEATURES, [round(float(v), 4) for v in x]))}
        self.history.setdefault(mid, deque(maxlen=240)).append((round(t, 1), round(score, 4), round(float(x[0]), 3), round(float(x[1]), 3)))
        thr = self.m["thresholds"]
        st.above_w = st.above_w + 1 if score >= thr["watch"] else 0
        st.above_c = st.above_c + 1 if score >= thr["critical"] else 0
        if st.above_w == 0 and st.above_c == 0:
            st.below += 1
            if st.below >= 20 and (st.watch_t or st.critical_t):      # cleared (e.g. after repair)
                st.watch_t = st.critical_t = None
        else:
            st.below = 0
        if st.above_w >= self.m["persist"]["watch"] and st.watch_t is None and st.critical_t is None:
            st.watch_t = t
            out.append(self._alert("watch", mid, x, score, t))
        if st.above_c >= self.m["persist"]["critical"] and st.critical_t is None:
            st.critical_t = t
            out.append(self._alert("critical", mid, x, score, t))
        self.events.extend(out)
        return out

    def explain(self, x: np.ndarray) -> list[dict]:
        phi = shapley(self.sf, x, self.m["background"])
        order = np.argsort(-np.abs(phi))
        return [{"signal": LABELS[FEATURES[i]], "feature": FEATURES[i], "shap": round(float(phi[i]), 4), "value": round(float(x[i]), 3)} for i in order]

    def rul(self, x: np.ndarray, score: float) -> dict:
        feats = np.append(x, score)[None, :]
        q = self.m["rul"]
        lo, med, hi = (float(np.exp(q[k].predict(feats)[0]) - 60) for k in ("q10", "q50", "q90"))
        lo, med, hi = max(0.0, lo), max(0.0, med), max(0.0, hi)
        return {"rul_s": round(med, 0), "rul_low_s": round(min(lo, med), 0), "rul_high_s": round(max(hi, med), 0)}

    def _alert(self, severity: str, mid: str, x: np.ndarray, score: float, t: float) -> dict:
        contrib = self.explain(x)
        a = {"type": "alert", "t": round(t, 1), "severity": severity, "machine": mid, "machine_id": mid, "score": round(score, 3),
             "contributors": contrib[:4], "vib_multiple": round(float(x[0]), 2), "detector": "isolation_forest+shap"}
        a.update(self.rul(x, score))
        top = ", ".join(f"{c['signal']} ({c['shap']:+.2f})" for c in contrib[:3])
        a["text"] = f"Anomaly detected on {mid} (score {score:.2f}): {top}"
        return a

    def current(self, mid: str) -> dict:
        st = self.state.get(mid)
        if not st or not st.last:
            return {"machine": mid, "score": None}
        return {"machine": mid, **st.last, "watch_t": st.watch_t, "critical_t": st.critical_t,
                "thresholds": self.m["thresholds"], "recent": list(self.history.get(mid, []))[-60:]}
