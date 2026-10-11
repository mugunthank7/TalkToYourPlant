"""Export the dashboard history from the engine.

Replaces the precomputed series in kpi.json (five scenarios) and the shift history in dashboard.json (30 days of shifts and
degradation incidents) with numbers produced by this engine. The 12-month maintenance statistics in dashboard.json are
estimates from the data generator and are kept as they are (the engine models one shift at a time).

    cd sim && .venv/bin/python -m plantsim.export          # writes data/out/{kpi,dashboard}.json and twin/public/data/
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from . import config as C
from .config import Params
from .model import HERO, PlantSim, ev, outputs_mod

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "out"
SCEN = {
    "ideal": dict(p=dict(ideal=True, hero_fault=False, micro_stops=False), about="Theoretical ceiling: no stops, no scrap, takt exactly 90 s."),
    "healthy_realistic": dict(p=dict(hero_fault=False), about="Normal day: micro-stops and base scrap, no faults."),
    "hero_timely_repair": dict(p=dict(hero_policy="timely", detector="hero"), about="M05 bearing wear caught by the anomaly detector, technician sent 5 min after the alert. The demo path."),
    "hero_delayed_repair": dict(p=dict(hero_policy="delayed", hero_delay_s=2400.0, detector="hero"), about="Same fault, repair starts 40 min late."),
    "hero_ignored": dict(p=dict(hero_policy="ignored", detector="hero"), about="Same fault, ignored: M05 seizes and the line waits for the emergency repair."),
}
START = dt.date(2026, 9, 1)
HIST_SEED = 2026


def _fault(onset_s: float | None, ramp_s: float | None):
    if onset_s is not None:
        ev.FAULT["onset_s"], ev.FAULT["ramp_s"] = onset_s, ramp_s


def _run(params: dict, onset_s: float | None = None, ramp_s: float | None = None) -> dict:
    """Run one shift in a worker process; returns the minute frame and what happened to the hero machine."""
    keep = (ev.FAULT["onset_s"], ev.FAULT["ramp_s"])
    _fault(onset_s, ramp_s)
    try:
        sim = PlantSim(Params(**params)).run()
    finally:
        ev.FAULT["onset_s"], ev.FAULT["ramp_s"] = keep
    crit = [a for a in sim.alerts if a.get("machine_id", a.get("machine")) == HERO and a.get("severity") == "critical"]
    wo = [w for w in sim.work_orders if w.machine == HERO]
    failed = any(e.get("type") == "fault" and e.get("machine") == HERO for e in sim.events)
    return {
        "frame": sim.minute_frame(), "alert_s": crit[0]["t"] if crit else None, "failed": failed,
        "repair_start_s": next((w.arrived_at for w in wo if w.arrived_at is not None), None),
        "repair_end_s": next((w.closed_at for w in wo if w.closed_at is not None), None),
        "onset_s": ev.FAULT["onset_s"] if onset_s is None else onset_s, "ramp_s": ev.FAULT["ramp_s"] if ramp_s is None else ramp_s,
    }


def _series(m) -> dict:
    n = np.arange(1, len(m) + 1)
    down = m["downtime_s"].cumsum()
    units, good = m["units_completed"].cumsum(), m["good_units"].cumsum()
    avail = 1 - down / (60 * n)
    perf = np.clip(C.Params().takt_s / m["effective_cycle_s"].expanding().mean(), 0, 1)
    qual = np.where(units > 0, good / np.maximum(units, 1), 1.0)
    return {"cum_units": units.tolist(), "cum_down_s": down.tolist(), "cum_cost": m["downtime_cost_usd"].cumsum().astype(int).tolist(),
            "oee": (avail * perf * qual).round(3).tolist(), "avail": avail.round(3).tolist(), "perf": perf.round(3).tolist(),
            "qual": np.round(qual, 3).tolist(), "cum_scrap": m["scrap_units"].cumsum().tolist()}


def scenarios(pool) -> tuple[dict, dict]:
    futs = {k: pool.submit(_run, dict(seed=C.Params().seed, **v["p"])) for k, v in SCEN.items()}
    series, summary = {}, {}
    for k, f in futs.items():
        r = f.result()
        m = r["frame"]
        series[k] = _series(m)
        summary[k] = outputs_mod.summary(m, takt_s=C.Params().takt_s) | {"about": SCEN[k]["about"]}
        if k.startswith("hero") and r["alert_s"] is not None:
            fail = r["onset_s"] + r["ramp_s"]
            summary[k] |= {"t_alert_s": r["alert_s"], "t_fail_if_ignored_s": fail, "remaining_useful_life_at_alert_min": round((fail - r["alert_s"]) / 60, 1),
                          "t_onset_s": r["onset_s"], "t_repair_start_s": r["repair_start_s"], "t_repair_end_s": r["repair_end_s"]}
    return series, summary


def history(pool, days: int = 30) -> tuple[list, list]:
    rng = np.random.default_rng(HIST_SEED)
    jobs = []
    for day in range(days):
        date = START + dt.timedelta(days=day)
        if date.weekday() == 6:
            continue
        takt = 120.0 if date.weekday() == 5 else 90.0
        eff = float(np.clip(rng.normal(0.97, 0.02), 0.9, 1.0))
        for shift in ("A", "B"):
            sid = f"{date.isoformat()}-{shift}"
            p = dict(seed=int(rng.integers(1, 2**31)), shift=shift, takt_s=takt, efficiency=eff, random_failures=True, hero_fault=False)
            inc = None
            if rng.random() < 0.15:
                onset, ramp = float(rng.uniform(0.3, 4.0) * 3600), float(rng.uniform(2.0, 3.5) * 3600)
                policy = str(rng.choice(["timely", "delayed", "ignored"], p=[0.55, 0.30, 0.15]))
                p |= dict(hero_fault=True, hero_policy=policy, detector="hero", hero_delay_s=(float(rng.uniform(1800, 2700)) if policy == "delayed" else 0.0))
                inc = (onset, ramp)
            jobs.append((sid, date, weekday := date.weekday(), shift, takt, p, inc, pool.submit(_run, p, *(inc or (None, None)))))
    shifts, incidents = [], []
    for sid, date, wd, shift, takt, p, inc, fut in jobs:
        r = fut.result()
        s = outputs_mod.summary(r["frame"], takt_s=takt)
        shifts.append({"shift_id": sid, "date": date.isoformat(), "weekday": wd, "shift": shift, "units": s["units"], "demand_plan_units": int(C.SHIFT_S / takt),
                       "oee": s["oee"], "availability": s["availability"], "performance": s["performance"], "quality": s["quality"],
                       "downtime_min": s["downtime_min"], "downtime_cost_usd": s["downtime_cost_usd"], "scrap_units": s["scrap_units"], "had_incident": inc is not None})
        if inc is not None:
            outcome = "failure" if r["failed"] else ("late" if p["hero_policy"] == "delayed" else "timely")
            incidents.append({"shift_id": sid, "date": date.isoformat(), "shift": shift, "machine_id": HERO, "component_id": ev.FAULT["component_id"],
                              "onset_s": int(inc[0]), "alert_s": None if r["alert_s"] is None else int(r["alert_s"]), "failure_s_if_ignored": int(inc[0] + inc[1]),
                              "outcome": outcome, "repair_start_s": r["repair_start_s"], "repair_end_s": r["repair_end_s"]})
    return shifts, incidents


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    with ProcessPoolExecutor() as pool:
        series, summary = scenarios(pool)
        shifts, incidents = history(pool, days)
    kpi = {"minutes": len(next(iter(series.values()))["cum_units"]), "plan_units": 320, "cost_per_min": C.COST_PER_MIN, "series": series, "summary": summary}
    (OUT / "kpi.json").write_text(json.dumps(kpi, separators=(",", ":")))
    dash = json.loads((OUT / "dashboard.json").read_text())
    dash |= {"scenario_summary": summary, "shifts": shifts, "incidents": incidents}
    (OUT / "dashboard.json").write_text(json.dumps(dash, separators=(",", ":")))
    for f in ("kpi.json", "dashboard.json"):
        shutil.copy(OUT / f, ROOT / "twin" / "public" / "data" / f)
    print(f"{'scenario':22s}{'units':>7s}{'OEE':>7s}{'down_min':>10s}{'cost_usd':>12s}")
    for k, s in summary.items():
        print(f"{k:22s}{s['units']:7d}{s['oee']:7.3f}{s['downtime_min']:10.1f}{s['downtime_cost_usd']:12,d}")
    print(f"{len(shifts)} shifts, {len(incidents)} incidents:", [(i['shift_id'][-7:], i['outcome']) for i in incidents])


if __name__ == "__main__":
    main()
