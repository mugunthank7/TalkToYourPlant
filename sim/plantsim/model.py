"""The plant as a SimPy discrete-event model.

Car bodies flow S04 -> S05 -> S06 -> S07 -> S09 on a paced line. Each station is a SimPy Resource with a
machine that can fail in the middle of a job. Segments between stations hold at most two cars, so a stopped
station really starves what is downstream and blocks what is upstream. Press and battery supply run
through finite buffers. Weld robot 2 follows the scripted bearing-wear curve; a technician and work orders
handle repairs. All randomness comes from named streams, so a replay with the same seed is identical until
something is changed (that is what makes what-if branching work).
"""
from __future__ import annotations

import itertools
import math
import zlib
from dataclasses import dataclass, field
from typing import Callable, Iterator

import numpy as np
import pandas as pd
import simpy

from . import config as C
from .config import Params

from plantdata import events as ev  # noqa: E402  (data package, path set up in config)
from plantdata import outputs as outputs_mod  # noqa: E402
from plantdata import sensors as sensors_mod  # noqa: E402

REPAIR_MIN = {"weld_robot": 25, "robot": 30, "press": 60, "fixture": 20, "vision_gate": 15, "gantry": 30,
              "sealer": 30, "decoiler": 40, "conveyor": 30, "agv": 15}
QDEPTH = int(__import__("os").environ.get("QDEPTH", "1"))
MICRO_X = float(__import__("os").environ.get("MICRO_X", "4.5"))   # micro-stop frequency multiplier, calibrated so everyday OEE matches the plant data (see tests)
HERO = ev.FAULT["machine_id"]
HERO_STATION = "S06"
PART_FOR = {"M05": "bearing_6208", "M04": "bearing_6208", "M01": "seal_kit_h40", "M03": "cyl_seal", "M06": "chain_set",
            "M07": "camera_unit", "M08": "servo_motor_a", "M09": "seal_head", "M10": "bearing_22222", "M02": "gripper_pad_set"}


@dataclass
class WorkOrder:
    id: str
    machine: str
    station: str
    kind: str                # predictive | breakdown | emergency
    opened_at: float
    dispatch_at: float
    repair_s: float
    part: str = ""
    status: str = "open"     # open | dispatched | on_site | closed
    arrived_at: float | None = None
    closed_at: float | None = None
    started_down_at: float | None = None

    def as_dict(self) -> dict:
        return {k: (round(v, 1) if isinstance(v, float) else v) for k, v in self.__dict__.items()}


class Station:
    def __init__(self, sim: "PlantSim", sid: str, name: str) -> None:
        self.sim, self.id, self.name = sim, sid, name
        self.env = sim.env
        self.res = simpy.Resource(sim.env, 1)
        self.down: dict[str, str] = {}           # machine id -> fault | repair | failed | micro
        self.fail_ev = sim.env.event()
        self.rep_ev: simpy.Event | None = None
        self.mode = "idle"                       # run | starved | blocked | idle
        self._since = sim.env.now
        self.acc = {"run": 0.0, "starved": 0.0, "blocked": 0.0, "idle": 0.0, "down": 0.0}
        self._down_since: float | None = None
        self.completed = 0
        self.last_cycle = 0.0

    # -- bookkeeping --------------------------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        now = self.env.now
        if now >= 0:
            self.acc[self.mode] += now - max(self._since, 0.0)
        self.mode, self._since = mode, now

    def is_down(self) -> bool:
        return bool(self.down)

    # -- machine events ----------------------------------------------------------------------
    def machine_down(self, mid: str, state: str) -> None:
        was = self.is_down()
        self.down[mid] = state
        if not was:
            ev_, self.fail_ev = self.fail_ev, self.env.event()
            ev_.succeed()
            self.rep_ev = self.env.event()
            self._down_since = self.env.now

    def machine_state(self, mid: str, state: str) -> None:
        if mid in self.down:
            self.down[mid] = state

    def machine_up(self, mid: str) -> None:
        self.down.pop(mid, None)
        if not self.down and self.rep_ev is not None:
            ev_, self.rep_ev = self.rep_ev, None
            ev_.succeed()
            if self._down_since is not None and self.env.now >= 0:
                self.acc["down"] += self.env.now - max(self._down_since, 0.0)
            self._down_since = None

    # -- doing work (interruptible) ---------------------------------------------------------------
    def work(self, duration: float) -> Iterator:
        remaining = duration
        while remaining > 1e-9:
            if self.is_down():
                yield self.rep_ev
                continue
            start = self.env.now
            tmo = self.env.timeout(remaining)
            yield tmo | self.fail_ev
            remaining -= self.env.now - start
        return None

    def state(self) -> tuple[str, str, str]:
        """(state, reason, machine) in the vocabulary the twin uses."""
        if self.down:
            mid, st = next(iter(self.down.items()))
            if st in ("fault", "failed"):
                return "fault", f"{mid} fault", mid
            if st == "repair":
                return "repair", f"{mid} under repair", mid
            return "micro", f"{mid} micro-stop", mid
        if self.mode == "starved":
            return "starved", "waiting for input", ""
        if self.mode == "blocked":
            return "blocked", "output full", ""
        return "run", "", ""


class Machine:
    def __init__(self, sim: "PlantSim", d: dict) -> None:
        self.sim, self.id, self.name, self.type = sim, d["id"], d["name"], d["type"]
        self.station = d["station"]
        self.state = "up"
        self.stations: list[Station] = []
        self.reset_degradation = False
        self.since = sim.env.now

    def fail(self, state: str = "fault") -> None:
        if self.state != "up":
            return
        self.state, self.since = state, self.sim.env.now
        for s in self.stations:
            s.machine_down(self.id, state)

    def set_state(self, state: str) -> None:
        self.state = state
        for s in self.stations:
            s.machine_state(self.id, state)

    def repair(self) -> None:
        self.state, self.since = "up", self.sim.env.now
        for s in self.stations:
            s.machine_up(self.id)


class PlantSim:
    def __init__(self, params: Params | None = None) -> None:
        self.p = params or Params()
        self.layout = C.layout()
        self.env = simpy.Environment(initial_time=-self.p.warm_s if self.p.warm_s else 0.0)
        self.events: list[dict] = []
        self.work_orders: list[WorkOrder] = []
        self._wo_n = itertools.count(1)
        self._car_n = itertools.count(1)
        self.hold_dispatch_until = -1.0
        self.takt = self.p.takt_s
        self.efficiency = self.p.efficiency
        self.station_speed: dict[str, float] = dict(self.p.station_speed)
        self.hero_policy = self.p.hero_policy
        self.hero_done = False
        self.wo_store = simpy.Store(self.env)
        self.cars: dict[int, dict] = {}
        self._rngs: dict[str, np.random.Generator] = {}
        # KPI counters (only from t = 0)
        self.completed = self.good = 0
        self.per_min: dict[int, dict] = {}
        self.line_down_s = 0.0
        self.cost = 0.0
        self.alerts: list[dict] = []
        self.cycle_mult_now = 1.0

        # stations and machines ---------------------------------------------------------------
        self.stations: dict[str, Station] = {s["id"]: Station(self, s["id"], s["name"]) for s in self.layout["stations"]}
        self.stations["BELT"] = Station(self, "BELT", "Conveyor")
        self.machines: dict[str, Machine] = {}
        for m in self.layout["machines"]:
            mach = Machine(self, m)
            self.machines[m["id"]] = mach
            if m["id"] == "M06":
                mach.stations = [self.stations[s] for s in (*C.BELT, "BELT")]
            else:
                mach.stations = [self.stations[m["station"]]]

        # buffers and segments ------------------------------------------------------------------
        self.blanks = simpy.Store(self.env, capacity=20)
        self.stamped = simpy.Store(self.env, capacity=14)
        self.packs = simpy.Store(self.env, capacity=2)
        cap = int(__import__("os").environ.get("SEG_CAP", "2"))
        self.seg = {("S04", "S05"): simpy.Resource(self.env, cap), ("S05", "S06"): simpy.Resource(self.env, cap),
                    ("S06", "S07"): simpy.Resource(self.env, cap), ("S07", "S09"): simpy.Resource(self.env, cap)}
        self.entry_wip = 0
        for _ in range(8):                                     # buffers start part full
            self.blanks.items.append(1)
        for _ in range(8):
            self.stamped.items.append(1)
        self.packs.items.append(1)

        self._start_processes()
        if self.p.warm_s:
            self.env.run(until=0.0)
        self._t0_wall = 0.0

    # -- randomness ------------------------------------------------------------------------------
    def rng(self, name: str) -> np.random.Generator:
        if name not in self._rngs:
            self._rngs[name] = np.random.default_rng([self.p.seed, zlib.crc32(name.encode())])
        return self._rngs[name]

    def service(self, sid: str, car: int) -> float:
        mean, std = C.service_stats(sid)
        if self.p.ideal:
            return mean
        s = std / mean
        r = self.rng(f"svc-{sid}-{car}")
        d = r.lognormal(math.log(mean) - s * s / 2, s)
        d *= C.speed_factor(sid, self.p.shift) * self.station_speed.get(sid, 1.0) / max(self.efficiency, 0.5)
        return float(np.clip(d, 0.5 * mean, 2.5 * mean))

    # -- processes -------------------------------------------------------------------------------
    def _start_processes(self) -> None:
        env = self.env
        env.process(self._supply("S01", self.blanks, None, "M10"))
        env.process(self._supply("S02", self.stamped, self.blanks, "M01"))
        env.process(self._supply("S08", self.packs, None, "M08"))
        env.process(self._release())
        env.process(self._technician())
        env.process(self._ticker())
        env.process(self._seed_cars())
        self.monitor = None
        self.hero_alert_ev = env.event()
        if self.p.detector:
            from .anomaly.detector import Monitor
            self.monitor = Monitor()
            env.process(self._health_monitor())
        if self.p.hero_fault:
            env.process(self._hero())
        if self.p.micro_stops and not self.p.ideal:
            for mid, prof in sensors_mod.PROFILE.items():
                env.process(self._micro_stops(mid, prof[6]))
        if self.p.random_failures and not self.p.ideal:
            for mid, mtbf in __import__("plantdata.maintenance", fromlist=["MTBF_H"]).MTBF_H.items():
                env.process(self._random_failures(mid, mtbf))
        for f in self.p.injected:
            env.process(self._injected(f))
        for c in self.p.changes:
            env.process(self._change(c))

    def _log(self, etype: str, **kw) -> None:
        self.events.append({"type": etype, "t": round(self.env.now, 1), **kw})

    def _supply(self, sid: str, out: simpy.Store, inp: simpy.Store | None, mid: str) -> Iterator:
        st = self.stations[sid]
        n = 0
        while True:
            if inp is not None:
                st.set_mode("starved")
                yield inp.get()
            n += 1
            st.set_mode("run")
            yield from st.work(self.service(sid, 100000 + n) if sid != "S01" else self.service("S01", n))
            st.set_mode("blocked")
            yield out.put(1)
            st.completed += 1

    def _slow(self) -> float:
        """Line speed factor: a derated machine slows the whole belt."""
        mult = 1.0
        m5 = self.machines.get(HERO)
        if m5 and self.p.hero_fault and not m5.reset_degradation and self.env.now >= ev.FAULT["onset_s"]:
            _, x = self._degr(self.env.now)
            mult = 1.0 + ev.FAULT["cycle_penalty"] * x
        self.cycle_mult_now = mult
        return mult

    def _release(self) -> Iterator:
        k = 0
        while True:
            yield self.env.timeout(self.takt * self._slow())
            st4 = self.stations["S04"]
            # strict pitch: if the first station is busy, down or has no parts, this slot is lost
            if st4.res.count + len(st4.res.queue) <= QDEPTH and not st4.is_down() and not self.stations["BELT"].is_down() and self.stamped.items:
                k += 1
                self.entry_wip += 1
                self.env.process(self._car(k))
            else:
                self._lost_pitch(self.takt * self.cycle_mult_now)

    def _culprit(self) -> str:
        st = self.stations
        for sid in (*C.LINE, "BELT"):
            if st[sid].is_down():
                return next(iter(st[sid].down))
        if not self.stamped.items:
            return "M01" if self.blanks.items else "M10"
        if st["S09"].mode == "starved" and not self.packs.items:
            return "M08"
        for sid in C.LINE:
            if st[sid].mode == "blocked":
                return {"S04": "M03", "S05": "M04", "S06": "M05", "S07": "M07", "S09": "M09"}[sid]
        return "M03"                                              # S04 itself is the pacing station

    def _lost_pitch(self, interval: float) -> None:
        """A paced slot passed with no car released: that is `interval` seconds of line downtime."""
        now = self.env.now
        if now <= 0:
            return
        who = self._culprit()
        a = max(0.0, now - interval)
        m = int(a // 60)
        t = a
        while t < now - 1e-9:
            nxt = min(now, (m + 1) * 60.0)
            b = self.per_min.setdefault(m, self._blank_bucket())
            b["down"] += nxt - t
            b["bottleneck"][who] = b["bottleneck"].get(who, 0) + (nxt - t)
            t, m = nxt, m + 1
        self.line_down_s += now - a
        self.cost += (now - a) * self.p.cost_per_min / 60.0
        self.lost_pitches = getattr(self, "lost_pitches", 0) + 1

    def _seed_cars(self) -> Iterator:
        # nothing to do: the warm-up pre-roll fills the line
        yield self.env.timeout(0)

    def _car(self, k: int) -> Iterator:
        env = self.env
        rec = {"k": k, "stage": "S04", "t_in": env.now, "q_pen": 0.0}
        self.cars[k] = rec
        route = ["S04", "S05", "S06", "S07", "S09"]
        st = self.stations[route[0]]
        rec["loc"] = "wait"
        req = st.res.request()
        yield req
        self.entry_wip -= 1
        held = (st, req)
        for i, sid in enumerate(route):
            st = self.stations[sid]
            rec["stage"], rec["loc"], rec["t_stage"] = sid, "work", env.now
            if sid == "S04":
                st.set_mode("starved")
                yield self.stamped.get()
            if sid == "S09":
                st.set_mode("starved")
                yield self.packs.get()
            st.set_mode("run")
            dur = self.service(sid, k)
            yield from st.work(dur)
            if sid == "S06" and self.p.hero_fault and not self.machines[HERO].reset_degradation:
                rec["q_pen"] = ev.FAULT["quality_penalty"] * self._degr(env.now)[1]
            st.completed += 1
            st.last_cycle = dur
            if i == len(route) - 1:
                break
            nxt = route[i + 1]
            seg = self.seg[(sid, nxt)]
            st.set_mode("blocked")
            rec["loc"] = "blocked"
            sreq = seg.request()
            yield sreq
            held[0].res.release(held[1])
            held[0].set_mode("idle")
            rec["loc"], rec["t_move"] = "transit", env.now
            rec["transit_s"] = C.item_s(sid, nxt) * (self._slow() if nxt != "S09" else 1.0)
            if nxt != "S09":
                yield from self.stations["BELT"].work(rec["transit_s"])
            else:
                yield env.timeout(rec["transit_s"])
            nst = self.stations[nxt]
            nreq = nst.res.request()
            rec["loc"] = "wait"
            yield nreq
            seg.release(sreq)
            held = (nst, nreq)
        held[0].res.release(held[1])
        held[0].set_mode("idle")
        self._complete(rec)
        self.cars.pop(k, None)

    def _complete(self, rec: dict) -> None:
        if self.env.now < 0:
            return
        scrap = (not self.p.ideal) and self.rng(f"scrap-{rec['k']}").random() < self.p.scrap_base + rec.get("q_pen", 0.0)
        self.completed += 1
        self.good += 0 if scrap else 1
        b = self.per_min.setdefault(int(self.env.now // 60), self._blank_bucket())
        b["done"] += 1
        b["good"] += 0 if scrap else 1

    @staticmethod
    def _blank_bucket() -> dict:
        return {"done": 0, "good": 0, "down": 0, "cycle_sum": 0.0, "n": 0, "bottleneck": {}}

    # -- machine events ------------------------------------------------------------------------------
    def _micro_stops(self, mid: str, gap: float) -> Iterator:
        r = self.rng(f"micro-{mid}")
        m = self.machines[mid]
        while True:
            yield self.env.timeout(r.exponential(gap / MICRO_X))
            dur = float(np.clip(r.lognormal(math.log(70), 0.5), 20, 300))
            if m.state == "up":
                m.fail("micro")
                yield self.env.timeout(dur)
                if m.state == "micro":
                    m.repair()

    def _random_failures(self, mid: str, mtbf_h: float) -> Iterator:
        r = self.rng(f"rand-{mid}")
        shape = 1.4
        scale = mtbf_h * 3600 / math.gamma(1 + 1 / shape)
        while True:
            yield self.env.timeout(float(scale * r.weibull(shape)))
            self._breakdown(mid, kind="breakdown")

    def _injected(self, f: dict) -> Iterator:
        yield self.env.timeout(max(0.0, f["t0"] - self.env.now))
        self._breakdown(f["machine"], kind="breakdown", repair_s=(f.get("repair_s") or None))

    def _breakdown(self, mid: str, kind: str = "breakdown", repair_s: float | None = None) -> None:
        m = self.machines[mid]
        if m.state not in ("up", "micro"):
            return
        if m.state == "micro":
            m.repair()
        m.fail("fault")
        self._log("fault", machine=mid, station=m.station, name=m.name)
        base = (REPAIR_MIN.get(m.type, 30) * 60.0) * float(self.rng(f"rep-{mid}-{int(self.env.now)}").lognormal(0, 0.25))
        self._open_wo(mid, kind, self.env.now + self.p.dispatch_delay_s, repair_s or base)

    def _open_wo(self, mid: str, kind: str, dispatch_at: float, repair_s: float) -> WorkOrder:
        m = self.machines[mid]
        wo = WorkOrder(id=f"WO-SIM-{next(self._wo_n):04d}", machine=mid, station=m.station, kind=kind, opened_at=self.env.now,
                       dispatch_at=dispatch_at, repair_s=repair_s, part=PART_FOR.get(mid, "consumables"))
        self.work_orders.append(wo)
        self._log("work_order", id=wo.id, machine=mid, station=m.station, kind=kind, spare_part=wo.part)
        self.wo_store.put(wo)
        return wo

    def _technician(self) -> Iterator:
        env = self.env
        while True:
            wo: WorkOrder = yield self.wo_store.get()
            while wo.dispatch_at > env.now:         # re-checked so a work order can be expedited while it waits
                yield env.timeout(min(30.0, wo.dispatch_at - env.now))
            while env.now < self.hold_dispatch_until:
                yield env.timeout(60)
            wo.status = "dispatched"
            self._log("dispatched", id=wo.id, machine=wo.machine)
            yield env.timeout(C.walk_s("S10", "S12") + 90.0 + C.walk_s("S12", wo.station))
            m = self.machines[wo.machine]
            wo.status, wo.arrived_at = "on_site", env.now
            if m.state in ("up", "micro"):
                if m.state == "micro":
                    m.repair()
                m.fail("repair")
                m.set_state("repair")
            else:
                m.set_state("repair")
            self._log("repair_start", id=wo.id, machine=wo.machine)
            yield env.timeout(wo.repair_s)
            if wo.machine == HERO:
                m.reset_degradation = True
                self.hero_done = True
            m.repair()
            wo.status, wo.closed_at = "closed", env.now
            self._log("repair_done", id=wo.id, machine=wo.machine)
            yield env.timeout(C.walk_s(wo.station, "S10"))

    # -- hero: bearing wear on weld robot 2 --------------------------------------------------------------
    def _degr(self, t: float) -> tuple[float, float]:
        d = float(ev.degradation(np.array([t]))[0])
        x = float(ev.progress(np.array([t]))[0])
        return d, x

    def _hero(self) -> Iterator:
        f = ev.FAULT
        t_alert, fail_t = ev.alert_time(), f["onset_s"] + f["ramp_s"]
        if self.monitor is not None:
            # real detection: wait for the Isolation Forest monitor to raise a critical alert on the hero machine
            yield self.hero_alert_ev
        else:
            yield self.env.timeout(max(0.0, f["onset_s"] - 1800 - self.env.now))
            self._alert("watch", "Vibration trending up on weld robot 2")
            yield self.env.timeout(max(0.0, t_alert - self.env.now))
            self._alert("critical", "Weld robot 2 bearing wear detected")
        policy = self.hero_policy
        fail_ev_t = fail_t
        if policy in ("timely", "delayed"):
            delay = self.p.dispatch_delay_s + (self.p.hero_delay_s if policy == "delayed" else 0.0)
            self._open_wo(HERO, "predictive", self.env.now + delay, self.p.hero_repair_s)
        # if nobody repaired it in time, it seizes
        yield self.env.timeout(max(0.0, fail_ev_t - self.env.now))
        m = self.machines[HERO]
        if not self.hero_done and m.state in ("up", "micro") and not any(w.machine == HERO and w.status in ("on_site", "closed") for w in self.work_orders):
            if m.state == "micro":
                m.repair()
            m.fail("failed")
            self._log("fault", machine=HERO, station=HERO_STATION, name=m.name, reason="bearing seized")
            # an open predictive WO (late) is superseded by an emergency one
            for w in self.work_orders:
                if w.machine == HERO and w.status in ("open", "dispatched"):
                    w.status = "closed"
            walk = C.walk_s("S10", "S12") + 90.0 + C.walk_s("S12", HERO_STATION)
            repair = max(600.0, self.p.emergency_total_s - self.p.dispatch_delay_s - walk)
            self._open_wo(HERO, "emergency", self.env.now + self.p.dispatch_delay_s, repair)

    def _alert(self, severity: str, text: str) -> None:
        d, x = self._degr(self.env.now)
        a = {"type": "alert", "t": round(self.env.now, 1), "severity": severity, "machine": HERO, "component_id": ev.FAULT["component_id"],
             "text": text, "vib_multiple": round(1 + ev.FAULT["vib_gain"] * d, 2),
             "rul_s": round(max(0.0, ev.FAULT["onset_s"] + ev.FAULT["ramp_s"] - self.env.now), 0)}
        self.alerts.append(a)
        self.events.append(a)

    # -- anomaly detection -----------------------------------------------------------------------------------
    def _health_monitor(self) -> Iterator:
        """Every 10 s note each machine's state; every minute build its telemetry and feed the streaming monitor."""
        from .health import Telemetry
        env = self.env
        mids = [HERO] if self.p.detector == "hero" else [m for m in self.machines if m in sensors_mod.PROFILE]
        clock0 = 6 * 3600 if self.p.shift == "A" else 14 * 3600
        tel = Telemetry(self.p.seed, clock0)
        marks = {m: [] for m in mids}

        def hero_degr(t):
            m5 = self.machines[HERO]
            if not self.p.hero_fault or m5.reset_degradation:
                return np.zeros(len(t)), np.zeros(len(t))
            return ev.degradation(t), ev.progress(t)

        while True:
            yield env.timeout(10.0)
            if env.now < 0:
                continue
            for mid in mids:
                mach = self.machines[mid]
                st = self.stations[mach.station]
                marks[mid].append((mach.state == "up", mach.state == "up" and st.mode == "run" and not st.is_down()))
            if round(env.now) % 60 == 0 and env.now > 0:
                for mid in mids:
                    ms = marks[mid][-6:]
                    marks[mid] = []
                    if len(ms) < 6:
                        continue
                    up = np.repeat([u for u, _ in ms], 10)
                    prod = np.repeat([p for _, p in ms], 10)
                    row = tel.minute(mid, env.now - 60.0, up, prod, hero_degr if mid == HERO else None)
                    for al in self.monitor.push(mid, row, env.now):
                        self.alerts.append(al)
                        self.events.append(al)
                        if mid == HERO and al["severity"] == "critical" and not self.hero_alert_ev.triggered:
                            self.hero_alert_ev.succeed()

    # -- what-if changes ---------------------------------------------------------------------------------
    def _change(self, c: dict) -> Iterator:
        yield self.env.timeout(max(0.0, c.get("at", self.env.now) - self.env.now))
        op = c["op"]
        if op == "keep_running":
            self.hold_dispatch_until = self.env.now + float(c.get("hours", 2.0)) * 3600
            self._log("change", op=op, hours=c.get("hours", 2.0))
        elif op == "dispatch_now":
            self._log("change", op=op)
            pend = [w for w in self.work_orders if w.machine == HERO and w.status == "open"]
            if pend:
                pend[0].dispatch_at = self.env.now          # expedite the order already raised instead of opening a second one
            elif not self.hero_done and not any(w.machine == HERO and w.status in ("dispatched", "on_site") for w in self.work_orders):
                self._open_wo(HERO, "predictive", self.env.now, self.p.hero_repair_s)
        elif op in ("add_operator", "remove_operator"):
            f = 0.75 if op == "add_operator" else 1.3
            self.station_speed[c["station"]] = self.station_speed.get(c["station"], 1.0) * f
            self._log("change", op=op, station=c["station"])
        elif op == "inject_fault":
            self._log("change", op=op, machine=c["machine"])
            self._breakdown(c["machine"], repair_s=(float(c["repair_min"]) * 60 if c.get("repair_min") else None))
        elif op == "set_takt":
            self.takt = float(c["takt_s"])
            self._log("change", op=op, takt_s=self.takt)
        elif op == "set_efficiency":
            self.efficiency = float(c["value"])
            self._log("change", op=op)
        elif op == "schedule_pm":
            m = self.machines[c["machine"]]
            if m.state in ("up", "micro"):
                m.repair() if m.state == "micro" else None
                m.fail("repair")
                m.set_state("repair")
                yield self.env.timeout(float(c.get("minutes", 30)) * 60)
                m.repair()
            self._log("change", op=op, machine=c["machine"])

    # -- KPI ticker ------------------------------------------------------------------------------------------
    def _ticker(self) -> Iterator:
        env = self.env
        while True:
            yield env.timeout(1.0)
            if env.now < 0:
                continue
            slow = self._slow()
            b = self.per_min.setdefault(int(env.now // 60), self._blank_bucket())
            b["n"] += 1
            b["cycle_sum"] += slow

    # -- running and reading ---------------------------------------------------------------------------------
    @property
    def now(self) -> float:
        return float(self.env.now)

    def run_until(self, t: float) -> None:
        if t > self.env.now:
            self.env.run(until=t)

    def run(self) -> "PlantSim":
        self.run_until(self.p.horizon_s)
        return self

    def minute_frame(self) -> pd.DataFrame:
        n = int(min(self.env.now, self.p.horizon_s) // 60)
        key = (n, self.completed, round(self.line_down_s))
        if getattr(self, "_mf_key", None) == key:
            return self._mf
        self._mf = self._build_frame(n)
        self._mf_key = key
        return self._mf

    def _build_frame(self, n: int) -> pd.DataFrame:
        rows, cum = [], 0
        for i in range(n):
            b = self.per_min.get(i) or self._blank_bucket()
            cum += b["done"]
            sec = max(b["n"], 1)
            cyc = self.takt * (b["cycle_sum"] / sec)
            avail = 1 - b["down"] / 60
            perf = float(np.clip(self.takt / cyc, 0, 1))
            qual = b["good"] / b["done"] if b["done"] else 1.0
            bn = max(b["bottleneck"], key=b["bottleneck"].get) if b["bottleneck"] else ""
            rows.append({"t_s": i * 60, "units_completed": b["done"], "good_units": b["good"], "scrap_units": b["done"] - b["good"],
                         "cum_units": cum, "line_up_s": 60 - b["down"], "downtime_s": b["down"], "effective_cycle_s": round(cyc, 1),
                         "availability": round(avail, 3), "performance": round(perf, 3), "quality": round(qual, 3),
                         "oee": round(avail * perf * qual, 3), "bottleneck_machine": bn,
                         "downtime_cost_usd": round(b["down"] / 60 * self.p.cost_per_min)})
        return pd.DataFrame(rows)

    def kpis(self) -> dict:
        m = self.minute_frame()
        if m.empty:
            return {"units": 0, "good_units": 0, "scrap_units": 0, "availability": 1.0, "performance": 1.0, "quality": 1.0, "oee": 1.0,
                    "downtime_min": 0.0, "downtime_cost_usd": 0, "units_per_hour_mean": 0.0, "ideal_units": 0.0, "units_lost_vs_ideal": 0.0}
        s = outputs_mod.summary(m, takt_s=self.p.takt_s)
        # the recorded minute frame is complete minutes only; add the partial current minute to the totals the API shows
        s["units_now"] = self.completed
        return s
