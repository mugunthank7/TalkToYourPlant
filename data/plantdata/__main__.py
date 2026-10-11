"""python -m plantdata --seed 42 --out out"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import events as ev
from . import layout as L
from . import history, maintenance, outputs, people, scenarios, schedule, transfers, validate


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
    summaries, sens = {}, {}
    for i, name in enumerate(scenarios.SCENARIOS):
        df, minutes, hourly, summ = scenarios.run(name, args.seed + 10 + i, hero)
        df.to_parquet(sdir / f"{name}_sensors.parquet", compression="zstd", index=False)
        minutes.to_parquet(sdir / f"{name}_output_minute.parquet", compression="zstd", index=False)
        hourly.to_csv(sdir / f"{name}_output_hourly.csv", index=False)
        summaries[name], sens[name] = summ, df
    validate.scenarios(summaries, sens)
    (sdir / "summary.json").write_text(json.dumps(summaries, indent=1))

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
        print("maintenance:", {k: v for k, v in mnt["stats"].items() if k not in ("per_machine", "line_down_h_by_category")})

    if args.copy_to:
        dst = Path(args.copy_to)
        dst.mkdir(parents=True, exist_ok=True)
        for f in ("layout.json", "schedule.json", "events.json"):
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
