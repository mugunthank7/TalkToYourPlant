"""Production output (throughput, OEE, scrap, downtime cost) derived from machine state.

Model: the body line and pack line are in series, so one stopped machine stops the line. The
press, transfer robot and decoiler sit upstream of a buffer, so their outages only stop the line
after BUFFER_S. A degrading weld robot derates its speed (longer cycle) and raises scrap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TAKT_S = 90.0
BASE_SCRAP = 0.015
BUFFER_S = 900
UPSTREAM = {"M01", "M02", "M10"}
# Siemens, The True Cost of Downtime 2024: large automotive plant, $2.3M per hour of unplanned downtime
# (they quote 'more than $600 a second'). 2.3M / 60 = ~$38,300 per minute. See docs/SOURCES.md.
DOWNTIME_COST_PER_MIN_USD = 38000


def _after_buffer(outage: np.ndarray, buffer_s: int) -> np.ndarray:
    """Seconds of an outage that go past what the buffer can absorb."""
    out = np.zeros_like(outage)
    n = len(outage)
    i = 0
    while i < n:
        if outage[i]:
            j = i
            while j < n and outage[j]:
                j += 1
            if j - i > buffer_s:
                out[i + buffer_s:j] = True
            i = j
        else:
            i += 1
    return out


def minute_frame(aux: dict, rng: np.random.Generator, takt_s: float = TAKT_S, efficiency: float = 1.0,
                 ideal: bool = False, cost_per_min: float = DOWNTIME_COST_PER_MIN_USD) -> pd.DataFrame:
    machines, up = aux["machines"], aux["up"]
    n = up.shape[1]
    line_ok = np.ones(n, dtype=bool)
    first_down = np.full(n, "", dtype=object)
    for i, m in enumerate(machines):
        outage = ~up[i]
        if m in UPSTREAM:
            outage = _after_buffer(outage, BUFFER_S)
        line_ok &= ~outage
        first_down = np.where(outage & (first_down == ""), m, first_down)

    cycle = takt_s / efficiency * aux["cycle_mult"]
    cum = np.cumsum(line_ok / cycle)
    mins = n // 60
    ends = cum[59::60][:mins]
    starts = np.concatenate([[0.0], ends[:-1]])
    done = np.floor(ends).astype(int) - np.floor(starts).astype(int)
    scrap_p = (0.0 if ideal else BASE_SCRAP) + aux["quality_pen"][:mins * 60].reshape(mins, 60).mean(axis=1)
    good = rng.binomial(done, np.clip(1 - scrap_p, 0, 1)) if not ideal else done.copy()
    down_s = (~line_ok[:mins * 60]).reshape(mins, 60).sum(axis=1)
    cyc_min = cycle[:mins * 60].reshape(mins, 60).mean(axis=1)
    availability = 1 - down_s / 60
    performance = np.clip(takt_s / cyc_min, 0, 1)
    quality = np.where(done > 0, good / np.maximum(done, 1), 1.0)
    bottleneck = [first_down[k * 60:(k + 1) * 60][first_down[k * 60:(k + 1) * 60] != ""] for k in range(mins)]
    bottleneck = [b[0] if len(b) else ("M05" if cyc_min[k] > takt_s * 1.02 else "") for k, b in enumerate(bottleneck)]
    return pd.DataFrame({
        "t_s": np.arange(mins) * 60,
        "units_completed": done,
        "good_units": good,
        "scrap_units": done - good,
        "cum_units": np.floor(ends).astype(int),
        "line_up_s": 60 - down_s,
        "downtime_s": down_s,
        "effective_cycle_s": cyc_min.round(1),
        "availability": availability.round(3),
        "performance": performance.round(3),
        "quality": quality.round(3),
        "oee": (availability * performance * quality).round(3),
        "bottleneck_machine": bottleneck,
        "downtime_cost_usd": (down_s / 60 * cost_per_min).round(0),
    })


def hourly(minutes: pd.DataFrame, ideal_per_hour: float) -> pd.DataFrame:
    g = minutes.assign(hour=minutes["t_s"] // 3600).groupby("hour")
    h = g.agg(units=("units_completed", "sum"), good_units=("good_units", "sum"), scrap_units=("scrap_units", "sum"),
              downtime_s=("downtime_s", "sum"), downtime_cost_usd=("downtime_cost_usd", "sum"),
              mean_cycle_s=("effective_cycle_s", "mean")).reset_index()
    h["availability"] = (1 - h["downtime_s"] / 3600).round(3)
    h["performance"] = (TAKT_S / h["mean_cycle_s"]).clip(upper=1).round(3)
    h["quality"] = (h["good_units"] / h["units"].where(h["units"] > 0, 1)).round(3)
    h["oee"] = (h["availability"] * h["performance"] * h["quality"]).round(3)
    h["units_vs_ideal"] = (h["units"] - ideal_per_hour).round(1)
    return h


def summary(minutes: pd.DataFrame, takt_s: float = TAKT_S) -> dict:
    secs = len(minutes) * 60
    ideal = secs / takt_s
    units, good = int(minutes["units_completed"].sum()), int(minutes["good_units"].sum())
    down = int(minutes["downtime_s"].sum())
    avail = 1 - down / secs
    perf = float(np.clip(takt_s / minutes["effective_cycle_s"].mean(), 0, 1))
    qual = good / units if units else 1.0
    return {
        "ideal_units": round(ideal, 1), "units": units, "good_units": good, "scrap_units": units - good,
        "units_lost_vs_ideal": round(ideal - units, 1),
        "availability": round(avail, 3), "performance": round(perf, 3), "quality": round(qual, 3),
        "oee": round(avail * perf * qual, 3), "downtime_min": round(down / 60, 1),
        "downtime_cost_usd": int(minutes["downtime_cost_usd"].sum()),
        "units_per_hour_mean": round(units / (secs / 3600), 1),
    }
