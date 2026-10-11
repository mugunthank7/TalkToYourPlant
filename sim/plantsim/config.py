"""Loads the generated data (layout, tasks, employees, transfer times) and the shared plantdata modules."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = DATA / "out"
if str(DATA) not in sys.path:
    sys.path.insert(0, str(DATA))

SHIFT_S = 8 * 3600
COST_PER_MIN = 38000

# Belt stations in order, then the end-of-line station.
BELT = ["S04", "S05", "S06", "S07"]
LINE = ["S04", "S05", "S06", "S07", "S09"]
UPSTREAM = ["S01", "S02", "S03"]


@dataclass
class Params:
    seed: int = 42
    shift: str = "A"
    takt_s: float = 90.0
    horizon_s: float = SHIFT_S
    micro_stops: bool = True
    random_failures: bool = False
    scrap_base: float = 0.015
    ideal: bool = False                 # no stops, no variance, no scrap: the theoretical ceiling
    hero_fault: bool = True             # weld robot 2 bearing wear (scripted degradation curve)
    hero_policy: str = "timely"         # timely | delayed | ignored
    hero_delay_s: float = 0.0           # extra delay before the technician is sent (policy delayed)
    efficiency: float = 1.0             # operator efficiency, scales service times by 1/efficiency
    dispatch_delay_s: float = 300.0
    emergency_total_s: float = 5400.0   # total downtime of an unplanned seize, from failure to restart
    hero_repair_s: float = 1500.0       # planned bearing replacement
    warm_s: float = 1500.0              # pre-roll before t=0 so the line starts full, like a running plant
    cost_per_min: float = COST_PER_MIN
    station_speed: dict = field(default_factory=dict)   # station id -> service time multiplier (0.8 = 20 percent faster)
    injected: list = field(default_factory=list)        # [{"machine","t0","repair_s"?}]
    changes: list = field(default_factory=list)         # what-if operations applied at their own time

    def copy(self, **kw) -> "Params":
        d = dict(self.__dict__)
        d["station_speed"] = dict(self.station_speed)
        d["injected"] = [dict(x) for x in self.injected]
        d["changes"] = [dict(x) for x in self.changes]
        d.update(kw)
        return Params(**d)


@lru_cache(maxsize=1)
def layout() -> dict:
    return json.loads((OUT / "layout.json").read_text())


@lru_cache(maxsize=1)
def hero_events() -> dict:
    return json.loads((OUT / "events.json").read_text())


@lru_cache(maxsize=1)
def tasks() -> pd.DataFrame:
    return pd.read_csv(OUT / "tasks.csv")


@lru_cache(maxsize=1)
def employees() -> pd.DataFrame:
    return pd.read_csv(OUT / "employees.csv")


@lru_cache(maxsize=1)
def transfers() -> pd.DataFrame:
    return pd.read_csv(OUT / "transfer_times.csv")


@lru_cache(maxsize=1)
def scenario_summary() -> dict:
    return json.loads((OUT / "scenarios" / "summary.json").read_text())


def walk_s(a: str, b: str) -> float:
    t = transfers()
    r = t[(t.kind == "walk") & (t.from_station == a) & (t.to_station == b)]
    return float(r.mean_s.iloc[0]) if len(r) else 60.0


def item_s(a: str, b: str) -> float:
    t = transfers()
    r = t[(t.kind == "item") & (t.from_station == a) & (t.to_station == b)]
    return float(r.mean_s.iloc[0]) if len(r) else 30.0


def service_stats(station: str) -> tuple[float, float]:
    """(mean, std) seconds of the cycle task at a station."""
    t = tasks()
    r = t[(t.station == station) & (t.trigger == "cycle")]
    if len(r):
        return float(r.mean_s.iloc[0]), float(r.std_s.iloc[0])
    return {"S01": (55.0, 8.0), "S03": (30.0, 5.0)}.get(station, (60.0, 8.0))


def speed_factor(station: str, shift: str) -> float:
    e = employees()
    r = e[(e["shift"] == shift) & (e["home_station"] == station) & (e["role"] == "operator")]
    return float(r.task_speed_factor.mean()) if len(r) else 1.0
