"""A year of estimated maintenance work orders and downtime events (2025-10-01 to 2026-09-30).

Everything here is an ESTIMATE built from typical industrial ranges, not measured data. The last
30 days reuse the incidents from history.py so the two files agree. Components are named
'<machine id lower>_<component>' (same convention as docs/STATIONS.md).
"""
from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from . import layout as L
from . import outputs

LABOR_USD_H = 65
SHIFT_START_H = {"A": 6, "B": 14}
START = dt.date(2025, 10, 1)
INCIDENT_FROM = dt.date(2026, 9, 1)
END = dt.date(2026, 9, 30)
UPSTREAM = outputs.UPSTREAM
BUFFER_MIN = outputs.BUFFER_S / 60

SUPPLIERS = ["Northwind Bearings", "Apex Hydraulics", "Meridian Drives", "Kestrel Robot Parts",
             "Orion Electrical", "Harbor Industrial Supply", "Lumen Vision Systems"]

# machine id -> mean operating hours between failures (estimate)
MTBF_H = {"M01": 700, "M02": 1800, "M03": 1500, "M04": 1400, "M05": 1400, "M06": 2500,
          "M07": 3000, "M08": 2000, "M09": 1800, "M10": 2500}

# type -> (mode, component, symptom, cause, repair procedure, spare part, supplier idx, weight, repair min, part $)
FAILURE_MODES = {
    "weld_robot": [
        ("bearing_wear", "joint1_bearing", "high vibration, rising temperature", "lubrication loss and fatigue", "Replace joint bearing and regrease", "bearing_6208", 0, 0.22, 90, 180),
        ("bearing_wear", "joint2_bearing", "high vibration, rising temperature", "lubrication loss and fatigue", "Replace joint bearing and regrease", "bearing_6208", 0, 0.08, 90, 180),
        ("servo_motor_fault", "servo_motor", "high motor current, overheating", "winding degradation", "Replace servo motor and recalibrate", "servo_motor_a", 2, 0.12, 150, 2400),
        ("gearbox_wear", "gearbox", "noise, backlash", "worn gear teeth", "Replace gearbox and retune", "gearbox_unit", 2, 0.08, 240, 3800),
        ("weld_tip_wear", "weld_gun", "weak welds, quality alarms", "electrode tip erosion", "Dress or replace electrode tips", "electrode_tips", 5, 0.28, 20, 40),
        ("cable_harness_fatigue", "cable_harness", "intermittent faults", "flex fatigue", "Replace cable harness", "cable_harness_kit", 3, 0.10, 75, 650),
        ("controller_fault", "controller_cabinet", "controller error codes", "I/O card failure", "Replace I/O card and reload program", "io_card", 4, 0.12, 60, 520),
    ],
    "robot": [
        ("gripper_fault", "gripper", "part drops", "pad wear and air leak", "Replace gripper pads and seals", "gripper_pad_set", 3, 0.35, 30, 220),
        ("bearing_wear", "joint1_bearing", "high vibration", "fatigue", "Replace joint bearing and regrease", "bearing_6208", 0, 0.25, 90, 180),
        ("servo_motor_fault", "servo_motor", "high motor current", "winding degradation", "Replace servo motor", "servo_motor_a", 2, 0.20, 150, 2400),
        ("controller_fault", "controller_cabinet", "controller error codes", "I/O card failure", "Replace I/O card", "io_card", 4, 0.20, 60, 520),
    ],
    "press": [
        ("hydraulic_leak", "hydraulic_unit", "pressure drop, oil on floor", "worn seals", "Replace seal kit and refill", "seal_kit_h40", 1, 0.30, 180, 900),
        ("die_wear", "die_insert", "part defects, burrs", "abrasive wear", "Replace die insert and re-shim", "die_insert_a", 5, 0.25, 240, 5200),
        ("clutch_brake_fault", "clutch_brake", "long stopping time", "friction pad wear", "Replace brake pads and recalibrate", "brake_pad_set", 5, 0.15, 300, 1400),
        ("lubrication_failure", "lube_pump", "high temperature, vibration", "pump failure", "Replace lube pump", "lube_pump", 1, 0.15, 90, 700),
        ("main_bearing_wear", "main_bearing", "vibration, noise", "overload and fatigue", "Replace main bearing", "bearing_22222", 0, 0.15, 360, 2600),
    ],
    "conveyor": [
        ("drive_chain_wear", "drive_chain", "jerky motion, noise", "elongation", "Replace drive chain", "chain_set", 5, 0.35, 90, 450),
        ("roller_seizure", "roller", "skid stalls", "bearing seizure", "Replace roller", "roller_unit", 5, 0.35, 45, 120),
        ("drive_motor_fault", "drive_motor", "high current, trips", "winding fault", "Replace drive motor", "drive_motor_b", 2, 0.15, 120, 900),
        ("sensor_misalignment", "position_sensor", "false stops", "vibration loosened mount", "Realign position sensor", "photo_eye", 4, 0.15, 20, 90),
    ],
    "fixture": [
        ("clamp_cylinder_leak", "clamp_cylinder", "slow clamping", "worn seal", "Replace cylinder seal", "cyl_seal", 1, 0.40, 45, 80),
        ("locating_pin_wear", "locating_pin", "gap and fit defects", "wear", "Replace locating pins", "pin_set", 5, 0.30, 30, 150),
        ("hydraulic_valve_fault", "valve", "unstable pressure", "contamination", "Replace valve", "valve_4_3", 1, 0.30, 75, 600),
    ],
    "vision_gate": [
        ("camera_fault", "camera", "no image", "sensor failure", "Replace camera", "camera_unit", 6, 0.35, 60, 1800),
        ("lens_contamination", "lens", "false rejects", "dust and spatter", "Clean lens", "cleaning_kit", 6, 0.45, 10, 5),
        ("calibration_drift", "camera", "measurement drift", "thermal drift", "Recalibrate", "none", 6, 0.20, 30, 0),
    ],
    "gantry": [
        ("belt_wear", "drive_belt", "positioning error", "wear", "Replace belt", "gantry_belt", 5, 0.40, 60, 140),
        ("linear_guide_wear", "linear_guide", "vibration", "wear", "Replace guide block", "guide_block", 0, 0.35, 120, 700),
        ("servo_motor_fault", "servo_motor", "high current", "winding fault", "Replace servo", "servo_motor_a", 2, 0.25, 120, 1500),
    ],
    "sealer": [
        ("seal_head_wear", "seal_head", "poor seals, leaks", "wear", "Replace seal head", "seal_head", 5, 0.40, 90, 520),
        ("heater_fault", "heater", "low temperature", "element burnout", "Replace heater", "heater_element", 4, 0.30, 60, 260),
        ("leak_tester_fault", "leak_tester", "false failures", "sensor drift", "Recalibrate or replace sensor", "pressure_sensor", 4, 0.30, 45, 300),
    ],
    "decoiler": [
        ("mandrel_bearing_wear", "mandrel_bearing", "vibration", "fatigue", "Replace mandrel bearing", "bearing_22222", 0, 0.50, 180, 2600),
        ("brake_fault", "brake", "uncontrolled uncoiling", "pad wear", "Replace brake pads", "brake_pad_set", 5, 0.30, 90, 1400),
        ("motor_fault", "motor", "high current", "winding fault", "Replace motor", "drive_motor_b", 2, 0.20, 150, 900),
    ],
}
TYPE_OF = {m[0]: m[2] for m in L.MACHINES}
STATION_OF = {m[0]: m[3] for m in L.MACHINES}
PM_MIN = {"weld_robot": 120, "robot": 90, "press": 180, "conveyor": 120, "fixture": 90, "vision_gate": 45,
          "gantry": 60, "sealer": 60, "decoiler": 60}


def _op_days(start: dt.date, end: dt.date) -> list[dt.date]:
    d, out = start, []
    while d <= end:
        if d.weekday() != 6:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def _line_down(machine: str, minutes: float) -> float:
    return max(0.0, minutes - BUFFER_MIN) if machine in UPSTREAM else minutes


def _pick_mode(rng: np.random.Generator, mtype: str):
    modes = FAILURE_MODES[mtype]
    w = np.array([m[7] for m in modes])
    return modes[int(rng.choice(len(modes), p=w / w.sum()))]


def build(seed: int, incidents: pd.DataFrame, cost_per_min: float) -> dict:
    rng = np.random.default_rng(seed)
    days = _op_days(START, INCIDENT_FROM - dt.timedelta(days=1))
    rows, down = [], []
    n_wo = 0

    def wo_id(ts: dt.datetime) -> str:
        nonlocal n_wo
        n_wo += 1
        return f"WO-{ts.year}-{n_wo:04d}"

    def add_corrective(mid: str, start: dt.datetime, mode, repair_min: float, wait_min: float, detected: str, planned: bool):
        _, comp, symptom, cause, proc, part, sup, _, _, part_cost = mode
        total = repair_min + wait_min
        ld = _line_down(mid, total)
        crew = 2 if repair_min > 120 else 1
        labor = repair_min / 60 * LABOR_USD_H * crew
        wid = wo_id(start)
        kind = "corrective_planned" if planned else "corrective_emergency"
        end = start + dt.timedelta(minutes=total)
        rows.append({"wo_id": wid, "opened_ts": start.isoformat(timespec="minutes"), "closed_ts": end.isoformat(timespec="minutes"),
                     "machine_id": mid, "component_id": f"{mid.lower()}_{comp}", "type": kind, "failure_mode": mode[0],
                     "symptom": symptom, "cause": cause, "repair_procedure": proc, "spare_part": part,
                     "supplier": SUPPLIERS[sup], "detected_by": detected, "crew": crew,
                     "labor_hours": round(repair_min / 60 * crew, 2), "parts_cost_usd": part_cost,
                     "labor_cost_usd": round(labor), "downtime_min": round(total, 1), "line_down_min": round(ld, 1),
                     "line_downtime_cost_usd": round(ld * cost_per_min)})
        down.append({"event_id": f"DT-{len(down) + 1:05d}", "start_ts": start.isoformat(timespec="minutes"),
                     "end_ts": end.isoformat(timespec="minutes"), "machine_id": mid, "station": STATION_OF[mid],
                     "category": "mechanical" if "motor" not in mode[0] and "controller" not in mode[0] and "heater" not in mode[0] and "camera" not in mode[0] else "electrical",
                     "cause": mode[0], "planned": planned, "duration_min": round(total, 1), "line_down_min": round(ld, 1), "wo_id": wid})

    # Random failures before the incident window (Weibull wear-out, shape 1.4) ----------
    shape = 1.4
    total_h = len(days) * 16
    for mid, mtbf in MTBF_H.items():
        mtype = TYPE_OF[mid]
        scale = mtbf / math.gamma(1 + 1 / shape)
        t = 0.0
        while True:
            t += scale * rng.weibull(shape)
            if t >= total_h:
                break
            day, hour = days[int(t // 16)], t % 16
            start = dt.datetime.combine(day, dt.time(6)) + dt.timedelta(hours=float(hour))
            mode = _pick_mode(rng, mtype)
            early = rng.random() < 0.45   # caught by an alarm or inspection before it stopped the line
            base = mode[8]
            if early:
                add_corrective(mid, start, mode, base * rng.uniform(0.5, 0.9), 0.0, "alarm", True)
            else:
                wait = float(rng.lognormal(math.log(240), 0.7)) if rng.random() < (0.15 if mode[9] > 1000 else 0.04) else 0.0
                add_corrective(mid, start, mode, base * rng.lognormal(0, 0.3), wait, "operator", False)

    # The incident window reuses history.py incidents -------------------------------
    for r in incidents.to_dict("records"):
        date = dt.date.fromisoformat(r["date"])
        t0 = dt.datetime.combine(date, dt.time(SHIFT_START_H[r["shift"]]))
        mid = r["machine_id"]
        comp = r["component_id"].split("_", 1)[1]
        mode = ("bearing_wear", comp, "high vibration, rising temperature", "lubrication loss and fatigue",
                "Replace bearing and regrease", "bearing_6208", 0, 1.0, 90, 180)
        if r["outcome"] == "failure":
            add_corrective(mid, t0 + dt.timedelta(seconds=r["failure_s_if_ignored"]), mode, 90, 0.0, "operator", False)
        else:
            add_corrective(mid, t0 + dt.timedelta(seconds=float(r["repair_start_s"])), mode, 25, 0.0, "predictive", True)

    # Non-maintenance downtime ---------------------------------------------------------
    all_days = _op_days(START, END)
    for kind, per_week, mean_min in (("material_shortage", 2.0, 18), ("quality_hold", 1.0, 35)):
        n = rng.poisson(per_week * len(all_days) / 6)
        for _ in range(n):
            day = all_days[int(rng.integers(len(all_days)))]
            start = dt.datetime.combine(day, dt.time(6)) + dt.timedelta(minutes=float(rng.uniform(0, 16 * 60)))
            m = float(np.clip(rng.lognormal(math.log(mean_min), 0.5), 5, 180))
            down.append({"event_id": f"DT-{len(down) + 1:05d}", "start_ts": start.isoformat(timespec="minutes"),
                         "end_ts": (start + dt.timedelta(minutes=m)).isoformat(timespec="minutes"), "machine_id": "",
                         "station": "S02" if kind == "material_shortage" else "S07", "category": kind, "cause": kind,
                         "planned": False, "duration_min": round(m, 1), "line_down_min": round(m, 1), "wo_id": ""})
    d = START + dt.timedelta(days=9)
    while d <= END:   # model changeover roughly every two weeks, planned
        if d.weekday() != 6:
            start = dt.datetime.combine(d, dt.time(6))
            down.append({"event_id": f"DT-{len(down) + 1:05d}", "start_ts": start.isoformat(timespec="minutes"),
                         "end_ts": (start + dt.timedelta(minutes=45)).isoformat(timespec="minutes"), "machine_id": "",
                         "station": "S04", "category": "changeover", "cause": "model_changeover", "planned": True,
                         "duration_min": 45.0, "line_down_min": 45.0, "wo_id": ""})
        d += dt.timedelta(days=14)

    # Preventive maintenance on Sundays (no production, so no line downtime) ----------------
    sundays = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)
               if (START + dt.timedelta(days=i)).weekday() == 6]
    seen_month: set = set()
    for s in sundays:
        key = (s.year, s.month)
        if key in seen_month:
            continue
        seen_month.add(key)
        quarterly = s.month in (1, 4, 7, 10)
        for mid in MTBF_H:
            mins = PM_MIN[TYPE_OF[mid]] * (2 if quarterly else 1)
            start = dt.datetime.combine(s, dt.time(8)) + dt.timedelta(minutes=int(rng.integers(0, 240)))
            parts = float(rng.uniform(150, 600)) if quarterly else float(rng.uniform(20, 120))
            rows.append({"wo_id": wo_id(start), "opened_ts": start.isoformat(timespec="minutes"),
                         "closed_ts": (start + dt.timedelta(minutes=mins)).isoformat(timespec="minutes"),
                         "machine_id": mid, "component_id": "", "type": "preventive_quarterly" if quarterly else "preventive_monthly",
                         "failure_mode": "", "symptom": "", "cause": "", "repair_procedure": "Lubricate, torque check, inspect wear parts",
                         "spare_part": "consumables", "supplier": SUPPLIERS[5], "detected_by": "schedule", "crew": 1,
                         "labor_hours": round(mins / 60, 2), "parts_cost_usd": round(parts), "labor_cost_usd": round(mins / 60 * LABOR_USD_H),
                         "downtime_min": float(mins), "line_down_min": 0.0, "line_downtime_cost_usd": 0})

    wo = pd.DataFrame(rows).sort_values("opened_ts").reset_index(drop=True)
    dt_ev = pd.DataFrame(down).sort_values("start_ts").reset_index(drop=True)
    dt_ev["event_id"] = [f"DT-{i + 1:05d}" for i in range(len(dt_ev))]
    modes = pd.DataFrame([{"machine_type": t, "failure_mode": m[0], "component": m[1], "symptom": m[2], "cause": m[3],
                           "repair_procedure": m[4], "spare_part": m[5], "supplier": SUPPLIERS[m[6]], "typical_repair_min": m[8],
                           "part_cost_usd": m[9]} for t, ms in FAILURE_MODES.items() for m in ms])
    return {"maintenance_work_orders": wo, "downtime_events": dt_ev, "failure_modes": modes, "stats": stats(wo, dt_ev, len(days) * 16)}


def stats(wo: pd.DataFrame, ev: pd.DataFrame, op_hours: float) -> dict:
    corr = wo[wo["type"].str.startswith("corrective")]
    per = {}
    for mid in MTBF_H:
        c = corr[corr["machine_id"] == mid]
        per[mid] = {"failures": int(len(c)), "mtbf_h_observed": round(op_hours / max(len(c), 1), 0),
                    "mttr_min": round(float(c["downtime_min"].mean()), 1) if len(c) else None,
                    "line_down_h": round(float(c["line_down_min"].sum()) / 60, 1)}
    unplanned = ev[~ev["planned"]]
    by_cat = unplanned.groupby("category")["line_down_min"].sum().sort_values(ascending=False)
    return {
        "period": f"{START} to {END}", "operating_hours_per_machine": op_hours,
        "work_orders": int(len(wo)), "corrective_work_orders": int(len(corr)),
        "emergency_share_of_corrective": round(float((corr["type"] == "corrective_emergency").mean()), 2),
        "unplanned_line_down_h": round(float(unplanned["line_down_min"].sum()) / 60, 1),
        "planned_line_down_h": round(float(ev[ev["planned"]]["line_down_min"].sum()) / 60, 1),
        "line_down_h_by_category": {k: round(v / 60, 1) for k, v in by_cat.items()},
        "maintenance_cost_usd": int((wo["parts_cost_usd"] + wo["labor_cost_usd"]).sum()),
        "line_downtime_cost_usd": int(wo["line_downtime_cost_usd"].sum()),
        "per_machine": per,
    }
