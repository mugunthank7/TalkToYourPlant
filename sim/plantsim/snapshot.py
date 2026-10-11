"""Live state of the simulated plant in the shape the twin and the LLM tools consume."""
from __future__ import annotations

import math
import zlib

import numpy as np

from . import config as C
from .model import HERO, PlantSim, sensors_mod, ev

D_BELT = {"S04": 5.0, "S05": 21.0, "S06": 37.0, "S07": 53.0}   # metres along the conveyor at each station
BELT_LEN = 59.0
CAR_GAP = 6.6          # metres between car centres: the body is about 4.7 m long, leaving a visible 1.9 m gap


def _noise(sim: PlantSim, mid: str, t: float, k: int) -> float:
    r = np.random.default_rng([sim.p.seed, zlib.crc32(mid.encode()), int(t), k])
    return float(r.normal())


def machine_sensors(sim: PlantSim, mid: str) -> dict:
    t = sim.now
    m = sim.machines[mid]
    prof = sensors_mod.PROFILE.get(mid)
    if not prof:
        return {}
    vib0, dtemp, cur0, duty, cycle, vnoise, _ = prof
    st = sim.stations[m.station]
    producing = m.state == "up" and st.mode == "run" and not st.is_down()
    if m.state != "up":
        load = 0.0
    else:
        phase = (zlib.crc32(mid.encode()) % 997) / 997 * cycle
        load = float(sensors_mod._load_curve(np.array([t]), duty, cycle, phase)[0]) if producing else 0.08
    d = x = 0.0
    if mid == HERO and sim.p.hero_fault and not m.reset_degradation:
        d, x = sim._degr(t)
    f = ev.FAULT
    vib = vib0 * (0.55 + 0.45 * load) * (1 + f["vib_gain"] * d) + vnoise * _noise(sim, mid, t, 0)
    band = 0.05 * vib0 * (0.7 + 0.3 * load) * (1 + f["band_gain"] * d) + abs(0.01 * vib0 * _noise(sim, mid, t, 1))
    ambient = 24 + 3 * math.sin(2 * math.pi * ((t + 6 * 3600) / 86400 - 0.3))
    temp = ambient + dtemp * (0.15 + 0.85 * load) + f["temp_rise_c"] * x + 0.15 * _noise(sim, mid, t, 2)
    cur = cur0 * (0.30 + 0.70 * load) * (1 + f["current_gain"] * d) + 0.01 * cur0 * _noise(sim, mid, t, 3)
    if m.state != "up":
        vib = 0.05
    return {"vibration_rms_mm_s": round(vib, 3), "vib_bpfo_band": round(band, 4), "temperature_c": round(temp, 2),
            "motor_current_a": round(cur, 2), "load_pct": round(load * 100, 1), "degradation": round(d, 4)}


def machine_info(sim: PlantSim, mid: str) -> dict:
    m = sim.machines[mid]
    out = {"id": mid, "name": m.name, "type": m.type, "station": m.station, "state": m.state, "since_s": round(m.since, 1),
           "sensors": machine_sensors(sim, mid), "reset": m.reset_degradation}
    if sim.monitor is not None and mid in sim.monitor.state:
        cur = sim.monitor.current(mid)
        out["anomaly"] = {k: cur.get(k) for k in ("score", "features", "watch_t", "critical_t", "thresholds")}
        crit = next((a for a in reversed(sim.alerts) if a["machine"] == mid and a["severity"] == "critical"), None)
        watch = next((a for a in reversed(sim.alerts) if a["machine"] == mid), None)
        out["alert"] = "critical" if crit and cur.get("critical_t") else "watch" if watch and cur.get("watch_t") else None
        if crit and cur.get("critical_t"):
            out["rul_s"] = max(0.0, crit["rul_s"] - (sim.now - crit["t"]))
            out["rul_range_s"] = [max(0.0, crit["rul_low_s"] - (sim.now - crit["t"])), max(0.0, crit["rul_high_s"] - (sim.now - crit["t"]))]
            out["contributors"] = crit["contributors"]
        if mid == HERO and sim.p.hero_fault and not m.reset_degradation:
            f = ev.FAULT
            d, x = sim._degr(sim.now)
            out["component_id"] = f["component_id"]
            out["degradation"] = round(d, 4)
            out["vib_multiple"] = round(1 + f["vib_gain"] * d, 2)
            out["ground_truth_rul_s"] = round(max(0.0, f["onset_s"] + f["ramp_s"] - sim.now), 0)
        return out
    if mid == HERO and sim.p.hero_fault and not m.reset_degradation:
        f = ev.FAULT
        d, x = sim._degr(sim.now)
        out["component_id"] = f["component_id"]
        out["degradation"] = round(d, 4)
        out["vib_multiple"] = round(1 + f["vib_gain"] * d, 2)
        if sim.now >= f["onset_s"]:
            out["rul_s"] = round(max(0.0, f["onset_s"] + f["ramp_s"] - sim.now), 0)
        out["alert"] = "critical" if sim.now >= ev.alert_time() else "watch" if sim.now >= f["onset_s"] - 1800 else None
    return out


NEXT = {"S04": "S05", "S05": "S06", "S06": "S07", "S07": "S09"}


def cars(sim: PlantSim) -> list[dict]:
    """Cars on the belt (d_m metres along it, `build` 0..1) and cars on their way to or at the pack station S09 (`exit` 0..1 along
    the body AGV route; 1 = at the marriage station). A car that has finished its transfer but still waits for the next station is
    shown at that station, not back at the one it left."""
    out, leaving = [], []
    for k, rec in sim.cars.items():
        sid = rec.get("stage")
        if sid not in D_BELT and sid != "S09":
            continue
        loc = rec.get("loc")
        moved = rec.get("t_move", -1.0) >= rec.get("t_stage", 0.0)       # has left `sid` in this stage cycle
        if sid == "S09" or (sid == "S07" and (loc == "transit" or (moved and loc == "wait"))):
            frac = 1.0
            if sid == "S07" and loc == "transit":
                frac = min(1.0, max(0.0, (sim.now - rec["t_move"]) / max(rec.get("transit_s", 1.0), 1.0)))
            leaving.append({"k": k, "stage": sid, "exit": round(frac, 3), "build": 1.0, "loc": loc})
            continue
        d = D_BELT[sid]
        if sid in NEXT and sid != "S07":
            if loc == "transit" and "t_move" in rec:
                frac = min(1.0, max(0.0, (sim.now - rec["t_move"]) / max(rec.get("transit_s", 1.0), 1.0)))
                d = D_BELT[sid] + (D_BELT[NEXT[sid]] - D_BELT[sid]) * frac
            elif moved and loc == "wait":
                d = D_BELT[NEXT[sid]]
        out.append({"k": k, "stage": sid, "d_m": d, "raw": d, "loc": loc})
    # Cars waiting at a station all have the station's position. Cars never overtake: the oldest car (lowest id) is in front, and
    # every younger car stands at least CAR_GAP behind the one ahead of it. Cars that would stand before the start of the belt
    # are not drawn yet. `build` is how far the car is built and painted (0 to 1), from where it would be without queueing.
    out.sort(key=lambda c: c["k"])
    for i in range(1, len(out)):
        out[i]["d_m"] = min(out[i]["d_m"], out[i - 1]["d_m"] - CAR_GAP)
    out = [c for c in out if c["d_m"] >= -2.5]
    for c in out:
        c["build"] = round(min(1.0, max(0.0, c.pop("raw") / D_BELT["S07"])), 3)
        c["d_m"] = round(c["d_m"], 2)
        c["progress"] = round(max(0.0, c["d_m"]) / BELT_LEN, 3)
    return out + leaving


def kpi_live(sim: PlantSim) -> dict:
    t = max(sim.now, 1.0)
    m = sim.minute_frame()
    if m.empty:
        return {"units": sim.completed, "good_units": sim.good, "oee": 1.0, "availability": 1.0, "performance": 1.0, "quality": 1.0,
                "downtime_min": 0.0, "downtime_cost_usd": 0, "throughput_per_hour": 0.0, "plan_units": 320}
    recent = m.tail(60)
    rate = float(recent.units_completed.sum()) / max(len(recent), 1) * 60
    secs = max(len(m) * 60, 1)
    down = float(m.downtime_s.sum())
    avail = 1 - down / secs
    perf = float(np.clip(sim.p.takt_s / m.effective_cycle_s.mean(), 0, 1))
    qual = (sim.good / sim.completed) if sim.completed else 1.0
    return {"units": sim.completed, "good_units": sim.good, "scrap_units": sim.completed - sim.good,
            "availability": round(avail, 3), "performance": round(perf, 3), "quality": round(qual, 3),
            "oee": round(avail * perf * qual, 3), "downtime_min": round(down / 60, 1),
            "downtime_cost_usd": int(down / 60 * sim.p.cost_per_min), "throughput_per_hour": round(rate, 1),
            "plan_units": int(sim.p.horizon_s / sim.p.takt_s), "t_s": round(t)}


def stations_info(sim: PlantSim) -> dict:
    t = max(sim.now, 1.0)
    out = {}
    line_fault = any(any(v != "micro" for v in sim.stations[x].down.values()) for x in (*C.LINE, "BELT"))
    for s in sim.layout["stations"]:
        st = sim.stations[s["id"]]
        state, reason, machine = st.state()
        if state in ("blocked", "starved"):
            dur = sim.now - max(st._since, 0.0)
            if s["id"] in ("S01", "S02", "S03", "S08"):
                if not line_fault:           # full supply buffers are normal, not a constraint
                    state, reason = "run", "buffer full"
            elif dur < 120:                  # short waits are part of normal flow
                state, reason = "run", ""
        elif state == "run" and st.mode == "idle" and s["id"] in C.LINE and sim.now - max(st._since, 0.0) >= 120:
            state, reason = "starved", "waiting for cars"
        # a fault in a belt station also stops the conveyor, so its neighbours show as waiting
        out[s["id"]] = {"name": s["name"], "state": state, "reason": reason, "machine": machine or None, "mode": st.mode,
                        "utilization": round(min(1.0, st.acc["run"] / t), 3), "completed": st.completed,
                        "last_cycle_s": round(st.last_cycle, 1)}
    return out


def snapshot(sim: PlantSim) -> dict:
    belt_down = [s for s in (*C.BELT, "BELT") if sim.stations[s].is_down()]
    return {
        "t": round(sim.now, 1),
        "stations": stations_info(sim),
        "machines": {mid: machine_info(sim, mid) for mid in sim.machines if mid in sensors_mod.PROFILE},
        "belt": {"moving": not belt_down, "cars": cars(sim), "speed_mult": round(1 / sim.cycle_mult_now, 3)},
        "buffers": {"blanks": len(sim.blanks.items), "stamped_sets": len(sim.stamped.items), "battery_packs": len(sim.packs.items)},
        "kpis": kpi_live(sim),
        "alerts": sim.alerts[-5:],
        "work_orders": [w.as_dict() for w in sim.work_orders[-8:]],
        "bottleneck": bottleneck(sim),
    }


def bottleneck(sim: PlantSim) -> dict:
    """Which station is the constraint right now, and what is at risk next."""
    st = stations_info(sim)
    util = {sid: v["utilization"] for sid, v in st.items() if sid in (*C.LINE, "S02", "S08")}
    worst = max(util, key=util.get) if util else None
    stopped = [sid for sid, v in st.items() if v["state"] in ("fault", "repair")]
    return {"pacing_station": worst, "utilization": util, "stopped": stopped,
            "hero_risk": machine_info(sim, HERO).get("alert")}
