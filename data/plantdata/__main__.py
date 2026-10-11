"""python -m plantdata --seed 42 --out out"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import events as ev
from . import layout as L
from . import history, maintenance, outputs, people, scenarios, schedule, transfers, validate


def kpi_json(mins: dict, summaries: dict) -> dict:
    """Per-minute cumulative KPIs for the twin's dashboard (cumulative OEE, units, downtime, cost)."""
    series = {}
    for name, m in mins.items():
        n = np.arange(1, len(m) + 1)
        down = m["downtime_s"].cumsum()
        units = m["units_completed"].cumsum()
        good = m["good_units"].cumsum()
        avail = 1 - down / (60 * n)
        perf = np.clip(outputs.TAKT_S / m["effective_cycle_s"].expanding().mean(), 0, 1)
        qual = np.where(units > 0, good / np.maximum(units, 1), 1.0)
        series[name] = {
            "cum_units": units.tolist(), "cum_down_s": down.tolist(),
            "cum_cost": m["downtime_cost_usd"].cumsum().astype(int).tolist(),
            "oee": (avail * perf * qual).round(3).tolist(),
            "avail": avail.round(3).tolist(), "perf": perf.round(3).tolist(), "qual": np.round(qual, 3).tolist(),
            "cum_scrap": (m["scrap_units"].cumsum()).tolist(),
        }
    return {"minutes": len(next(iter(mins.values()))), "plan_units": 320,
            "cost_per_min": outputs.DOWNTIME_COST_PER_MIN_USD, "series": series, "summary": summaries}


def dashboard_json(hist: dict, mnt: dict, summaries: dict) -> dict:
    """Everything the in-depth KPI tab needs, in one small file."""
    shifts = hist["history_shifts"][["shift_id", "date", "weekday", "shift", "units", "demand_plan_units", "oee",
                                      "availability", "performance", "quality", "downtime_min", "downtime_cost_usd",
                                      "scrap_units", "had_incident"]].round(3)
    ev = mnt["downtime_events"]
    unplanned = ev[~ev["planned"]]
    by_machine = unplanned[unplanned["machine_id"] != ""].groupby("machine_id")["line_down_min"].sum().div(60).round(1)
    by_cause = unplanned.groupby("cause")["line_down_min"].sum().div(60).round(1).sort_values(ascending=False).head(10)
    monthly = ev.assign(month=ev["start_ts"].str[:7]).groupby("month")["line_down_min"].sum().div(60).round(1)
    return {
        "machines": [{"id": m[0], "name": m[1], "type": m[2], "station": m[3]} for m in L.MACHINES],
        "scenario_summary": summaries,
        "shifts": json.loads(shifts.to_json(orient="records")),
        "incidents": json.loads(hist["history_incidents"].to_json(orient="records")),
        "maintenance": mnt["stats"],
        "downtime_h_by_machine": by_machine.to_dict(),
        "downtime_h_by_cause": by_cause.to_dict(),
        "downtime_h_by_month": monthly.to_dict(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="out")
    ap.add_argument("--history-days", type=int, default=30)
    ap.add_argument("--skip-history", action="store_true")
    ap.add_argument("--copy-to", default=None, help="also copy small JSON files here (e.g. ../twin/public/data)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    g = L.build_graph()
    validate.layout(g)
    (out / "layout.json").write_text(json.dumps(L.to_json(g), indent=1))

    roster = people.make_roster(rng)
    roster.to_csv(out / "employees.csv", index=False)
    people.tasks_frame().to_csv(out / "tasks.csv", index=False)
    transfers.build(g).to_csv(out / "transfer_times.csv", index=False)

    tech = roster[(roster["shift"] == ev.FAULT["shift"]) & (roster["role"] == "technician")].iloc[0]
    hero = ev.hero_timeline(g, float(tech["walk_speed_mps"]))
    (out / "events.json").write_text(json.dumps(hero, indent=1))

    shifts = {}
    coverage = {}
    for shift in people.SHIFTS:
        srng = np.random.default_rng(rng.integers(1 << 31))
        ppl = schedule.build_shift(roster, shift, g, srng, hero)
        coverage[shift] = validate.schedule(ppl)
        shifts[shift] = ppl
    (out / "schedule.json").write_text(json.dumps(
        {"meta": {"seed": args.seed, "shift_seconds": schedule.SHIFT_S, "takt_s": schedule.TAKT_S,
                  "note": "t is seconds since shift start; coordinates are metres (x east, z south)"},
         "shifts": shifts}, separators=(",", ":")))

    sdir = out / "scenarios"
    sdir.mkdir(exist_ok=True)
    summaries, sens, mins = {}, {}, {}
    for i, name in enumerate(scenarios.SCENARIOS):
        df, minutes, hourly, summ = scenarios.run(name, args.seed + 10 + i, hero)
        df.to_parquet(sdir / f"{name}_sensors.parquet", compression="zstd", index=False)
        minutes.to_parquet(sdir / f"{name}_output_minute.parquet", compression="zstd", index=False)
        hourly.to_csv(sdir / f"{name}_output_hourly.csv", index=False)
        summaries[name], sens[name], mins[name] = summ, df, minutes
    validate.scenarios(summaries, sens)
    (sdir / "summary.json").write_text(json.dumps(summaries, indent=1))
    (out / "kpi.json").write_text(json.dumps(kpi_json(mins, summaries), separators=(",", ":")))

    if not args.skip_history:
        hdir = out / "history"
        hdir.mkdir(exist_ok=True)
        hist = history.build(args.history_days, args.seed + 100)
        validate.history(hist)
        for name, frame in hist.items():
            if name in ("history_sensors_1min", "history_hourly"):
                frame.to_parquet(hdir / f"{name}.parquet", compression="zstd", index=False)
            else:
                frame.to_csv(hdir / f"{name}.csv", index=False)
        mnt = maintenance.build(args.seed + 200, hist["history_incidents"], outputs.DOWNTIME_COST_PER_MIN_USD)
        validate.maintenance(mnt)
        for name in ("maintenance_work_orders", "downtime_events", "failure_modes"):
            mnt[name].to_csv(hdir / f"{name}.csv", index=False)
        (hdir / "maintenance_stats.json").write_text(json.dumps(mnt["stats"], indent=1))
        (out / "dashboard.json").write_text(json.dumps(dashboard_json(hist, mnt, summaries), separators=(",", ":")))
        print("maintenance:", {k: v for k, v in mnt["stats"].items() if k not in ("per_machine", "line_down_h_by_category")})

    if args.copy_to:
        dst = Path(args.copy_to)
        dst.mkdir(parents=True, exist_ok=True)
        for f in ("layout.json", "schedule.json", "events.json", "kpi.json", "dashboard.json"):
            if not (out / f).exists():
                continue
            (dst / f).write_bytes((out / f).read_bytes())

    print(f"employees: {len(roster)}  tasks: {len(people.TASKS)}")
    print("hero:", {k: v for k, v in hero.items() if k.startswith("t_")})
    print("station coverage (shift A):", coverage["A"])
    print(f"{'scenario':22s}{'units':>7s}{'lost':>7s}{'OEE':>7s}{'down_min':>10s}{'cost_usd':>12s}")
    for n, v in summaries.items():
        print(f"{n:22s}{v['units']:7d}{v['units_lost_vs_ideal']:7.0f}{v['oee']:7.3f}{v['downtime_min']:10.1f}{v['downtime_cost_usd']:12,d}")
    for f in sorted(out.rglob("*")):
        if f.is_file():
            print(f"  {str(f.relative_to(out)):46s}{f.stat().st_size / 1024:9.0f} KB")


if __name__ == "__main__":
    main()
