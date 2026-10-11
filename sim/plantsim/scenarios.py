"""What-if runner: replay to now (deterministic), apply changes at now, run to the horizon, compare to the unchanged future."""
from __future__ import annotations

from . import config as C
from .config import Params
from .model import PlantSim


def _curve(sim: PlantSim, every: int = 10) -> list[int]:
    m = sim.minute_frame()
    return [int(v) for v in m.cum_units.iloc[every - 1::every]]


def run_branch(base: Params, changes: list[dict] | None = None, now_s: float | None = None) -> dict:
    p = base.copy(changes=[dict(c) for c in (changes or [])], detector=("hero" if base.detector else False))
    for c in p.changes:
        c.setdefault("at", now_s if now_s is not None else 0.0)
    sim = PlantSim(p).run()
    k = sim.kpis()
    return {"kpis": k, "cum_units_10min": _curve(sim), "events": sim.events[-30:], "work_orders": [w.as_dict() for w in sim.work_orders]}


_POOL = None


def _pool():
    global _POOL
    if _POOL is None:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor
        _POOL = ProcessPoolExecutor(max_workers=2, mp_context=mp.get_context("spawn"))
    return _POOL


def what_if_fast(base: Params, changes: list[dict], now_s: float) -> dict:
    """what_if with the two branches run in worker processes: in parallel, and without competing with the API's event loop
    for the interpreter lock (in the server, a what-if took 60 s with browser clients connected, 7 s alone)."""
    try:
        pool = _pool()
        fb, fs = pool.submit(run_branch, base, [], now_s), pool.submit(run_branch, base, changes, now_s)
        return _combine(base, changes, now_s, fb.result(), fs.result())
    except Exception:       # noqa: BLE001  (pool broken or cannot spawn: fall back to this process)
        return what_if(base, changes, now_s)


def _combine(base: Params, changes: list[dict], now_s: float, baseline: dict, scenario: dict) -> dict:
    b, s = baseline["kpis"], scenario["kpis"]
    keys = ("units", "good_units", "oee", "availability", "downtime_min", "downtime_cost_usd", "units_lost_vs_ideal")
    delta = {k: round(s[k] - b[k], 3) for k in keys if k in s and k in b}
    return {"now_s": now_s, "changes": changes, "baseline": baseline, "scenario": scenario, "delta": delta,
            "summary": narrate(b, s, delta, changes)}


def what_if(base: Params, changes: list[dict], now_s: float) -> dict:
    """Baseline = nothing changes from now on. Scenario = the changes apply at `now_s`."""
    return _combine(base, changes, now_s, run_branch(base, [], now_s), run_branch(base, changes, now_s))


def narrate(b: dict, s: dict, d: dict, changes: list[dict]) -> str:
    what = ", ".join(_describe(c) for c in changes) or "no changes"
    cars = int(d.get("units", 0))
    cost = int(d.get("downtime_cost_usd", 0))
    word = "more" if cars >= 0 else "fewer"
    cw = "extra" if cost >= 0 else "saved"
    return (f"With {what}: {s['units']} cars instead of {b['units']} ({abs(cars)} {word}), "
            f"downtime {s['downtime_min']:.0f} min vs {b['downtime_min']:.0f} min, "
            f"OEE {s['oee']*100:.0f}% vs {b['oee']*100:.0f}%, {abs(cost):,} dollars {cw} in downtime cost.")


def _describe(c: dict) -> str:
    op = c.get("op", "")
    if op == "keep_running":
        return f"the alert ignored for {c.get('hours', 2)} h"
    if op == "dispatch_now":
        return "the technician sent now"
    if op in ("add_operator", "remove_operator"):
        return f"{op.replace('_', ' ')} at {c.get('station')}"
    if op == "inject_fault":
        return f"a breakdown of {c.get('machine')}"
    if op == "set_takt":
        return f"takt {c.get('takt_s')} s"
    if op == "schedule_pm":
        return f"planned maintenance of {c.get('machine')} for {c.get('minutes', 30)} min"
    return op or "a change"
