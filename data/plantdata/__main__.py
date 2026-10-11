"""python -m plantdata --seed 42 --out out"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import events as ev
from . import layout as L
from . import people, schedule, sensors, transfers, validate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="out")
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

    df = sensors.generate(schedule.SHIFT_S, np.random.default_rng(args.seed + 1), True, hero)
    validate.sensors(df, True)
    df.to_parquet(out / "sensors_shiftA_fault.parquet", compression="zstd", index=False)
    healthy = sensors.generate(schedule.SHIFT_S, np.random.default_rng(args.seed + 2), False, None)
    validate.sensors(healthy, False)
    healthy.to_parquet(out / "sensors_healthy_train.parquet", compression="zstd", index=False)

    if args.copy_to:
        dst = Path(args.copy_to)
        dst.mkdir(parents=True, exist_ok=True)
        for f in ("layout.json", "schedule.json", "events.json"):
            (dst / f).write_bytes((out / f).read_bytes())

    print(f"employees: {len(roster)}  tasks: {len(people.TASKS)}")
    print("hero:", {k: v for k, v in hero.items() if k.startswith("t_")})
    print("station coverage (shift A):", coverage["A"])
    for f in sorted(out.iterdir()):
        print(f"  {f.name:34s}{f.stat().st_size / 1024:9.0f} KB")


if __name__ == "__main__":
    main()
