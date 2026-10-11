"""Tools the LLM side can call. Each has a JSON schema (function-calling style) and a handler."""
from __future__ import annotations

import pandas as pd

from . import config as C
from .model import HERO, ev
from .scenarios import what_if_fast as what_if
from .snapshot import bottleneck, kpi_live, machine_info, snapshot, stations_info

TOOLS: list[dict] = [
    {"name": "get_plant_state", "description": "Current state of the whole plant: every station (run, starved, blocked, repair, fault), live KPIs, buffers, alerts, open work orders and the pacing station.",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "get_station", "description": "State and utilisation of one station and its machines.",
     "parameters": {"type": "object", "properties": {"station_id": {"type": "string", "description": "S01 to S12"}}, "required": ["station_id"]}},
    {"name": "get_machine_health", "description": "Sensors, degradation, remaining useful life and alert level of one machine.",
     "parameters": {"type": "object", "properties": {"machine_id": {"type": "string", "description": "M01 to M10"}}, "required": ["machine_id"]}},
    {"name": "get_anomaly_report", "description": "Machine-learning anomaly detector output (Isolation Forest trained on healthy data): anomaly score, alert level, SHAP-style top contributing signals, predicted remaining useful life with an 80% interval, and recent score history. Omit machine_id for all machines.",
     "parameters": {"type": "object", "properties": {"machine_id": {"type": "string", "description": "M01 to M10, optional"}}}},
    {"name": "get_kpis", "description": "Live OEE, availability, performance, quality, throughput, downtime and its cost.",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "get_diagnosis_context", "description": "Everything needed to diagnose a machine: sensor trends, alerts, work orders, affected stations, likely failure modes from the knowledge catalogue and what happens if we wait versus act now.",
     "parameters": {"type": "object", "properties": {"machine_id": {"type": "string"}}, "required": ["machine_id"]}},
    {"name": "run_what_if", "description": "Simulate a change from now to the end of the shift and compare with doing nothing. Ops: keep_running {hours}, dispatch_now, add_operator {station}, remove_operator {station}, inject_fault {machine, repair_min}, set_takt {takt_s}, schedule_pm {machine, minutes}.",
     "parameters": {"type": "object", "properties": {"changes": {"type": "array", "items": {"type": "object"}}}, "required": ["changes"]}},
    {"name": "create_work_order", "description": "Open a corrective work order for a machine so a technician is dispatched.",
     "parameters": {"type": "object", "properties": {"machine_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["machine_id"]}},
    {"name": "inject_fault", "description": "Demo control: break a machine right now.",
     "parameters": {"type": "object", "properties": {"machine_id": {"type": "string"}, "repair_minutes": {"type": "number"}}, "required": ["machine_id"]}},
]


def _failure_modes(mtype: str) -> list[dict]:
    p = C.OUT / "history" / "failure_modes.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    return df[df.machine_type == mtype][["failure_mode", "component", "symptom", "cause", "repair_procedure", "spare_part"]].to_dict("records")


def diagnosis_context(live, machine_id: str) -> dict:
    sim = live.sim
    m = sim.machines[machine_id]
    info = machine_info(sim, machine_id)
    st = stations_info(sim)
    affected = [{"station": sid, "state": v["state"], "reason": v["reason"]} for sid, v in st.items() if v["state"] != "run"]
    trend = []
    if machine_id == HERO and sim.p.hero_fault and not m.reset_degradation:
        for back in (3600, 2700, 1800, 900, 0):
            t = max(0.0, sim.now - back)
            d, x = sim._degr(t)
            trend.append({"minutes_ago": back // 60, "vib_multiple": round(1 + ev.FAULT["vib_gain"] * d, 2)})
    s = info.get("sensors", {})
    evidence = []
    if "vib_multiple" in info:
        evidence.append(f"Vibration is {info['vib_multiple']}x its healthy level and {'rising' if trend and trend[-1]['vib_multiple'] > trend[0]['vib_multiple'] else 'steady'}.")
        evidence.append(f"Bearing-defect band energy {s.get('vib_bpfo_band')} (healthy is about 0.06), temperature {s.get('temperature_c')} C, motor current {s.get('motor_current_a')} A.")
        if "rul_s" in info:
            evidence.append(f"Remaining useful life if left running: about {int(info['rul_s'] // 60)} minutes.")
    evidence.append(f"Machine state: {m.state}. Station {m.station} is {st[m.station]['state']}.")
    out = {"machine": info, "sensor_trend": trend, "evidence": evidence, "affected_stations": affected,
           "open_work_orders": [w.as_dict() for w in sim.work_orders if w.machine == machine_id and w.status != "closed"],
           "recent_events": [e for e in sim.events if e.get("machine") == machine_id][-8:],
           "candidate_failure_modes": _failure_modes(m.type), "component_ids": [info.get("component_id")] if info.get("component_id") else []}
    if machine_id == HERO and not sim.hero_done:
        wi = what_if(live.params, [{"op": "dispatch_now"}], sim.now)
        wait = what_if(live.params, [{"op": "keep_running", "hours": 2}], sim.now)
        out["decision"] = {"act_now": wi["summary"], "wait_two_hours": wait["summary"],
                           "cost_of_waiting_usd": int(wait["scenario"]["kpis"]["downtime_cost_usd"] - wi["scenario"]["kpis"]["downtime_cost_usd"])}
    return out


def anomaly_report(sim, machine_id: str | None = None) -> dict:
    mon = getattr(sim, "monitor", None)
    if mon is None:
        return {"error": "anomaly detector not running"}
    ids = [machine_id] if machine_id else list(mon.state)
    if machine_id and machine_id not in sim.machines:
        return {"error": f"unknown machine {machine_id}"}
    out = {}
    for mid in ids:
        info = machine_info(sim, mid)
        out[mid] = {"anomaly": info.get("anomaly"), "alert": info.get("alert"), "contributors": info.get("contributors"),
                    "rul_s": info.get("rul_s"), "rul_range_s": info.get("rul_range_s"),
                    "history": [{"t": h[0], "score": h[1], "vib_ratio": h[2], "band_ratio": h[3]} for h in list(mon.history.get(mid, []))[-60:]]}
    thr = mon.m["thresholds"]
    res = {"thresholds": thr, "model": "IsolationForest on load-normalised features, healthy-only training", "machines": out}
    return {"machine_id": machine_id, **out[machine_id], "thresholds": thr} if machine_id else res


def call_tool(live, name: str, args: dict) -> dict:
    sim = live.sim
    if name == "get_plant_state":
        return snapshot(sim)
    if name == "get_station":
        sid = args["station_id"]
        info = stations_info(sim).get(sid)
        if info is None:
            return {"error": f"unknown station {sid}"}
        return {"station": sid, **info, "machines": [machine_info(sim, m["id"]) for m in sim.layout["machines"] if m["station"] == sid and m["id"] in sim.machines and m["id"] != "M11"]}
    if name == "get_machine_health":
        if args["machine_id"] not in sim.machines:
            return {"error": f"unknown machine {args['machine_id']}"}
        return machine_info(sim, args["machine_id"])
    if name == "get_anomaly_report":
        return anomaly_report(sim, args.get("machine_id"))
    if name == "get_kpis":
        return {**kpi_live(sim), "bottleneck": bottleneck(sim)}
    if name == "get_diagnosis_context":
        return diagnosis_context(live, args["machine_id"])
    if name == "run_what_if":
        return what_if(live.params, args.get("changes", []), sim.now)
    if name == "create_work_order":
        wo = live.create_work_order(args["machine_id"], args.get("reason", "requested"))
        return wo
    if name == "inject_fault":
        return live.inject(args["machine_id"], args.get("repair_minutes"))
    return {"error": f"unknown tool {name}"}
