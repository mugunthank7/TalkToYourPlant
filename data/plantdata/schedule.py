"""Per-person timelines for one shift: where each person is, what they do, and when.

Each segment is contiguous with the previous one. Kinds: walk, work, wait, fetch, break,
inspect, audit, observe, maintain, repair, pickup, standby, desk. `anim` is the animation the
3D scene should play: walk, work, crouch or idle.
"""
from __future__ import annotations

import math
import zlib

import numpy as np
import pandas as pd

from . import events as ev
from . import layout as L
from .people import OPERATOR_STATIONS, TASK_BY_STATION

TAKT_S = 90.0
SHIFT_S = 8 * 3600
FETCH_EVERY = {"S02": ("S03", "T-FETCH-PARTS", 12), "S04": ("S03", "T-FETCH-PARTS", 12),
               "S05": ("S12", "T-FETCH-TIPS", 20), "S06": ("S12", "T-FETCH-TIPS", 20)}
TASK_STATS = {"T-S02-LOAD": (70, 10), "T-S04-LOAD": (85, 12), "T-S05-WELD": (70, 9), "T-S06-WELD": (70, 9),
              "T-S07-CHECK": (55, 8), "T-S08-STACK": (80, 12), "T-S09-SEAL": (75, 10), "T-FETCH-PARTS": (40, 8),
              "T-FETCH-TIPS": (45, 8)}

BREAK_START, BREAK_GAP, BREAK_S = 1.5 * 3600, 18 * 60, 15 * 60
LUNCH_START, LUNCH_GAP, LUNCH_S = 4.0 * 3600, 30 * 60, 25 * 60


class Timeline:
    def __init__(self, emp: dict, graph: L.Graph, rng: np.random.Generator) -> None:
        self.emp, self.g, self.rng = emp, graph, rng
        self.speed = float(emp["walk_speed_mps"])
        self.segs: list[dict] = []
        self.t = 0.0
        self.at = "GATE"
        self.dx = 0.0
        self.pos = self.g.xy("GATE")
        self.face_pt: list[float] | None = None
        self.inside: str | None = None
        self.seat = zlib.crc32(emp["employee_id"].encode())

    # positions -------------------------------------------------------------
    def _xy(self, place: str, dx: float) -> tuple[float, float]:
        x, z = self.g.xy(self.g.node_for(place))
        return (x + dx, z)

    def _face(self, place: str) -> list[float]:
        if self.face_pt is not None:
            return self.face_pt
        if place == "GATE":
            return [self.g.xy("A14")[0], 40.0]
        s = L.station(place)
        return [s["x"], s["z"]]

    def _spot(self, place: str, kind: str | None):
        spots = L.STATION_SPOTS.get((place, kind)) if kind else None
        if not spots:
            return None
        sx, sz, fx, fz = spots[self.seat % len(spots)]
        s = L.station(place)
        return (s["x"] + sx, s["z"] + sz, s["x"] + fx, s["z"] + fz)

    def _doors(self, place: str) -> list[tuple[float, float]]:
        s = L.station(place)
        return [(s["x"] + dx, s["z"] + dz) for dx, dz in L.DOORS.get(place, [])]

    # actions ---------------------------------------------------------------
    def walk_time(self, dest: str) -> float:
        pts = self.g.polyline(self.at, dest)
        return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) / self.speed

    def walk_to(self, dest: str, dx: float = 0.0, kind: str | None = None) -> None:
        spot = self._spot(dest, kind)
        target = (spot[0], spot[1]) if spot else self._xy(dest, dx)
        same = dest == self.at and math.dist(self.pos, target) < 1e-6
        if same:
            return
        pts: list[tuple[float, float]] = [self.pos]
        if self.inside:
            pts += list(reversed(self._doors(self.inside)))
        pts += self.g.polyline(self.at if not self.inside else self.inside, dest)
        if spot:
            pts += self._doors(dest)
        pts.append(target)
        clean = [pts[0]]
        for p in pts[1:]:
            if math.dist(p, clean[-1]) > 1e-6:
                clean.append(p)
        length = sum(math.dist(clean[i], clean[i + 1]) for i in range(len(clean) - 1))
        dur = max(length / self.speed, 0.1)
        self.segs.append({"k": "walk", "s": self.t, "e": self.t + dur, "anim": "walk",
                          "path": [[round(a, 2), round(b, 2)] for a, b in clean], "to": dest})
        self.t += dur
        self.at, self.dx, self.pos = dest, dx, target
        self.inside = dest if spot else None
        self.face_pt = [spot[2], spot[3]] if spot else None

    def do(self, kind: str, dur: float, task: str | None = None, anim: str = "idle") -> None:
        if dur <= 0:
            return
        if self.face_pt is not None and anim in ("idle", "work") and self.at == "S11" and kind in ("break", "lunch", "desk"):
            anim = "sit"
        x, z = self.pos
        self.segs.append({"k": kind, "s": self.t, "e": self.t + dur, "anim": anim, "station": self.at,
                          "task": task, "at": [round(x, 2), round(z, 2)], "face": self._face(self.at)})
        self.t += dur

    def hold_until(self, t: float, kind: str = "wait", anim: str = "idle", task: str | None = None) -> None:
        if t > self.t:
            self.do(kind, t - self.t, task, anim)

    # helpers ---------------------------------------------------------------
    def duration(self, task: str) -> float:
        mean, std = TASK_STATS[task]
        s = std / mean
        d = self.rng.lognormal(math.log(mean) - s * s / 2, s) * float(self.emp["task_speed_factor"])
        return float(np.clip(d, 0.5 * mean, TAKT_S - 8))


def work_cycles(tl: Timeline, station: str, t_end: float, dx: float, counter: dict) -> None:
    """Run the station's takt cycles until t_end. Includes periodic fetch trips."""
    task = TASK_BY_STATION[station]
    offset = (OPERATOR_STATIONS.index(station) * 17) % TAKT_S if station in OPERATOR_STATIONS else 0
    tl.walk_to(station, dx)
    while tl.t < t_end - 1e-6:
        g = offset + math.ceil((tl.t - offset) / TAKT_S) * TAKT_S
        if g > tl.t:
            tl.hold_until(min(g, t_end), "wait")
            if tl.t >= t_end - 1e-6:
                break
        d = tl.duration(task)
        tl.do("work", min(d, t_end - tl.t), task, "work")
        counter[station] = counter.get(station, 0) + 1
        if station in FETCH_EVERY and counter[station] % FETCH_EVERY[station][2] == 0 and t_end - tl.t > 150:
            fetch_station, fetch_task, _ = FETCH_EVERY[station]
            tl.walk_to(fetch_station)
            tl.do("fetch", tl.duration(fetch_task), fetch_task, "work")
            tl.walk_to(station, dx)


def plan_breaks(roster: pd.DataFrame, shift: str, g: L.Graph) -> dict:
    ops = roster[(roster["shift"] == shift) & (roster["role"] == "operator")].reset_index(drop=True)
    plan = []
    for i, e in ops.iterrows():
        tw = g.distance(e["home_station"], "S11") / float(e["walk_speed_mps"])
        for start, gap, dur in ((BREAK_START, BREAK_GAP, BREAK_S), (LUNCH_START, LUNCH_GAP, LUNCH_S)):
            leave = start + i * gap
            plan.append({"emp": e["employee_id"], "station": e["home_station"], "leave": leave,
                         "back": leave + 2 * tw + dur, "dur": dur, "kind": "break" if dur == BREAK_S else "lunch"})
    return {"ops": ops, "plan": sorted(plan, key=lambda p: p["leave"])}


def dx_for(roster: pd.DataFrame, emp_id: str) -> float:
    e = roster[roster["employee_id"] == emp_id].iloc[0]
    same = roster[(roster["shift"] == e["shift"]) & (roster["role"] == "operator") &
                  (roster["home_station"] == e["home_station"])]["employee_id"].tolist()
    return 0.0 if len(same) == 1 else (-1.5 if same.index(emp_id) == 0 else 1.5)


def build_shift(roster: pd.DataFrame, shift: str, g: L.Graph, rng: np.random.Generator, hero: dict | None) -> list[dict]:
    people = roster[roster["shift"] == shift]
    bp = plan_breaks(roster, shift, g)
    out: list[dict] = []

    def emp_rows(role: str) -> list[dict]:
        return people[people["role"] == role].to_dict("records")

    # Operators ------------------------------------------------------------
    for e in emp_rows("operator"):
        tl = Timeline(e, g, rng)
        dx = dx_for(roster, e["employee_id"])
        counter: dict = {}
        mine = [p for p in bp["plan"] if p["emp"] == e["employee_id"]]
        for p in mine:
            work_cycles(tl, e["home_station"], p["leave"], dx, counter)
            tl.walk_to("S11", kind=p["kind"])
            tl.do(p["kind"], p["dur"], "T-BREAK" if p["kind"] == "break" else "T-LUNCH", "idle")
        work_cycles(tl, e["home_station"], SHIFT_S, dx, counter)
        out.append(finish(tl))

    # Relief operator covers every break window -------------------------------
    rel = emp_rows("relief_operator")[0]
    tl = Timeline(rel, g, rng)
    counter = {}
    tl.walk_to("S11", kind="standby")
    for i, p in enumerate(bp["plan"]):
        tw = g.distance(tl.at, p["station"]) / tl.speed
        if tl.t < p["leave"] - tw:
            tl.hold_until(p["leave"] - tw, "standby")
        work_cycles(tl, p["station"], p["back"], dx_for(roster, p["emp"]), counter)
        nxt = bp["plan"][i + 1]["leave"] if i + 1 < len(bp["plan"]) else SHIFT_S
        if nxt - tl.t > 150:
            tl.walk_to("S11", kind="standby")
    tl.hold_until(SHIFT_S, "standby")
    out.append(finish(tl))

    # Event-driven roles -----------------------------------------------------
    def breaks(offset: float) -> list[tuple[float, callable]]:
        def brk(tl: Timeline) -> None:
            tl.walk_to("S11", kind="break"); tl.do("break", BREAK_S, "T-BREAK")

        def lunch(tl: Timeline) -> None:
            tl.walk_to("S11", kind="lunch"); tl.do("lunch", LUNCH_S + 300, "T-LUNCH")
        return [(2.0 * 3600 + offset, brk), (3.6 * 3600 + offset, lunch)]

    def run(e: dict, evts: list[tuple[float, callable]], home: str, idle_kind: str) -> dict:
        tl = Timeline(e, g, rng)
        tl.walk_to(home, kind=idle_kind)
        for t, fn in sorted(evts, key=lambda x: x[0]):
            if t >= SHIFT_S:
                continue
            tl.walk_to(home, kind=idle_kind)
            tl.hold_until(t, idle_kind)
            fn(tl)
        tl.walk_to(home, kind=idle_kind)
        tl.hold_until(SHIFT_S, idle_kind)
        return finish(tl)

    insp = emp_rows("inspector")[0]

    def qa_round(tl: Timeline) -> None:
        tl.walk_to("S07"); tl.do("inspect", float(np.clip(tl.rng.normal(300, 40), 200, 400)), "T-QA-SAMPLE", "work")
        tl.walk_to("S06"); tl.do("audit", 120, "T-QA-AUDIT", "work")
        tl.walk_to("S05"); tl.do("audit", 120, "T-QA-AUDIT", "work")
    out.append(run(insp, [(600 + k * 1800, qa_round) for k in range(16)] + breaks(0), "S07", "wait"))

    sup = emp_rows("supervisor")[0]

    def line_walk(tl: Timeline) -> None:
        for st in ("S04", "S05", "S06", "S07"):
            tl.walk_to(st); tl.do("observe", 60, "T-SUP-WALK")

    def react(tl: Timeline) -> None:
        tl.walk_to("S06"); tl.do("observe", 240, "T-SUP-WALK")
    sup_events = [(1200 + k * 2700, line_walk) for k in range(11)] + breaks(300)
    if hero and shift == ev.FAULT["shift"]:
        sup_events.append((hero["t_alert_s"] + 60, react))
    out.append(run(sup, sup_events, "S11", "desk"))

    tech = emp_rows("technician")[0]

    def pm(station: str) -> callable:
        def fn(tl: Timeline) -> None:
            tl.walk_to(station); tl.do("maintain", float(np.clip(tl.rng.normal(420, 60), 300, 600)), "T-PM-CHECK", "crouch")
        return fn

    def repair(tl: Timeline) -> None:
        tl.walk_to("S12", kind="pickup"); tl.do("pickup", ev.PICKUP_S, None, "work")
        tl.walk_to("S06"); tl.do("repair", ev.REPAIR_S, "T-REPAIR-BEARING", "crouch")
    tech_events = [(p["t_s"], pm(p["station"])) for p in (hero or ev.hero_timeline(g, 1.3))["preventive_maintenance"]]
    tech_events += breaks(600)
    if hero and shift == ev.FAULT["shift"]:
        tech_events.append((hero["t_dispatch_s"], repair))
    out.append(run(tech, tech_events, "S10", "desk"))
    return out


def finish(tl: Timeline) -> dict:
    """Clip to the shift, merge adjacent identical segments, round."""
    segs = []
    for s in tl.segs:
        if s["s"] >= SHIFT_S:
            continue
        s = dict(s)
        if s["e"] > SHIFT_S and s["k"] != "walk":
            s["e"] = SHIFT_S
        segs.append(s)
    merged: list[dict] = []
    for s in segs:
        p = merged[-1] if merged else None
        if p and s["k"] != "walk" and (p["k"], p.get("station"), p.get("task"), p.get("at")) == (
                s["k"], s.get("station"), s.get("task"), s.get("at")) and abs(p["e"] - s["s"]) < 1e-6:
            p["e"] = s["e"]
        else:
            merged.append(s)
    for s in merged:
        s["s"], s["e"] = round(s["s"], 2), round(s["e"], 2)
    # Make contiguity exact after rounding.
    for i in range(1, len(merged)):
        merged[i]["s"] = merged[i - 1]["e"]
    e = tl.emp
    return {"employee_id": e["employee_id"], "name": e["name"], "role": e["role"], "shift": e["shift"],
            "home_station": e["home_station"], "timeline": merged}
