"""Maintenance work orders, daily checks, vendor service logs, incidents/RCAs, handover notes, spare parts."""
import datetime as dt
import math
import random
from collections import defaultdict

from .catalog import AREAS, FAMILIES, FAMILY_BY_KEY, PLANT
from .people import AS_OF, SOP_DATE, VENDOR_SLA, ESCALATION_TEMPLATE, FIRST_NAMES, LAST_NAMES

START = dt.date(2024, 10, 1)
END = AS_OF

SHIFT_HOURS = {"A": (6, 14), "B": (14, 22), "C": (22, 30)}   # C runs past midnight
SHIFT_WEIGHTS = {"A": 0.36, "B": 0.36, "C": 0.28}

# Machines with a recurring problem ("bad actors") and storylines used in the demo
BAD_ACTORS = {
    # machine_id: (fault_code, extra_events_per_year, window_start, window_end)
    "CAS-GP-01": ("GP-SHOT-SLOW", 7, dt.date(2025, 6, 1), dt.date(2026, 10, 10)),
    "PNT-PR-04": ("PR-BELL-SPEED", 6, dt.date(2025, 9, 1), dt.date(2026, 10, 10)),
    "BAT-BL-01": ("LSR-PWR-LOW", 9, dt.date(2025, 3, 1), dt.date(2026, 10, 10)),
    "BIW-WK-03": ("KSS-GEAR-LEAK", 5, dt.date(2025, 11, 1), dt.date(2026, 10, 10)),
    "UTL-CP-02": ("CMP-DISCH-TEMP", 6, dt.date(2025, 5, 1), dt.date(2026, 10, 10)),
    "STP-PRS-02": ("PRS-DOUBLE-BLANK", 8, dt.date(2025, 1, 1), dt.date(2026, 6, 30)),
    "GA-TQ-07": ("TQ-NOK", 10, dt.date(2025, 8, 1), dt.date(2026, 10, 10)),
    "BIW-WF-02": ("SRVO-065", 3, dt.date(2025, 1, 1), dt.date(2026, 10, 10)),
}

ROOT_CAUSE_KEYWORDS = [
    (("lubric", "grease"), "Lubrication"), (("contamin", "dirty", "clog", "fouled", "loaded", "debris"), "Contamination"),
    (("wear", "worn", "fatigue", "aging", "degrad", "elongation", "bearing"), "Wear / aging"),
    (("battery", "encoder", "sensor", "cable", "contactor", "terminal", "thermocouple", "connector", "amplifier",
      "drive fault", "relay", "voltage", "supply"), "Electrical / instrumentation"),
    (("operator", "skipped", "misplaced", "fixture", "part"), "Operator / material handling"),
    (("parameter", "calibration", "setting", "program", "software", "threshold", "payload", "offset", "checksum"),
     "Software / configuration"),
    (("cooling", "water flow", "refrigerant", "cooler", "duty"), "Thermal / cooling"),
    (("leak", "seal", "hose", "fitting"), "Leak / sealing"),
    (("drift", "variation", "growth", "sensitivity", "concentration", "buildup", "deposit"), "Process drift"),
]


def root_cause_category(text):
    t = text.lower()
    for kws, cat in ROOT_CAUSE_KEYWORDS:
        if any(k in t for k in kws):
            return cat
    return "Unknown / under investigation"


def rand_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def lc_first(s):
    return s[0].lower() + s[1:] if s else s


def past(action):
    """Turn an imperative action into a short past-tense technician phrase (best effort)."""
    verbs = {"Replace": "Replaced", "Check": "Checked", "Inspect": "Inspected", "Clean": "Cleaned", "Clear": "Cleared",
             "Re-master": "Re-mastered", "Re-teach": "Re-taught", "Verify": "Verified", "Run": "Ran", "Record": "Recorded",
             "Measure": "Measured", "Reset": "Reset", "Review": "Reviewed", "Apply": "Applied", "Back": "Backed",
             "Validate": "Validated", "Break": "Broke", "Calibrate": "Calibrated", "Realign": "Realigned",
             "Isolate": "Isolated", "Pull": "Pulled", "Flush": "Flushed", "Stop": "Stopped", "Re-level": "Re-levelled",
             "Identify": "Identified", "Locate": "Located", "Compare": "Compared", "Allow": "Allowed",
             "Monitor": "Monitored", "Take": "Took", "Swap": "Swapped", "Restart": "Restarted", "Re-home": "Re-homed",
             "Re-localize": "Re-localized", "Update": "Updated", "De-energize": "De-energized", "Reseat": "Reseated",
             "Trend": "Trended", "Perform": "Performed", "Schedule": "Scheduled", "Plan": "Planned", "Sample": "Sampled",
             "Vibration": "Vibration analysis done:", "Repeat": "Repeated", "Do": "Did", "Pressure": "Pressure-tested"}
    first, _, rest = action.partition(" ")
    if first in verbs:
        return f"{verbs[first]} {rest}".strip()
    return action


def pick_weighted(rng, items, weights):
    return rng.choices(items, weights=weights, k=1)[0]


def working_days(a, b):
    d = a
    out = []
    while d <= b:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def sample_dt(rng, day, shift=None):
    shift = shift or pick_weighted(rng, list(SHIFT_WEIGHTS), list(SHIFT_WEIGHTS.values()))
    lo, hi = SHIFT_HOURS[shift]
    minutes = rng.randint(lo * 60, hi * 60 - 1)
    base = dt.datetime.combine(day, dt.time(0, 0)) + dt.timedelta(minutes=minutes)
    return base, shift


def shift_of(ts):
    h = ts.hour
    return "A" if 6 <= h < 14 else ("B" if 14 <= h < 22 else "C")


class Index:
    def __init__(self, machines, emps, assignments):
        self.m = {m["machine_id"]: m for m in machines}
        self.emp = {e["employee_id"]: e for e in emps}
        self.asg = defaultdict(lambda: defaultdict(list))
        for a in assignments:
            self.asg[(a["machine_id"], a["shift"])][a["role"]].append(a["employee_id"])

    def who(self, mid, shift, role, rng, n=1):
        lst = self.asg[(mid, shift)].get(role) or self.asg[(mid, "ALL")].get(role) or []
        if not lst:
            return None
        return lst[rng.randrange(len(lst))]

    def name(self, eid):
        return self.emp[eid]["name"] if eid else "Unknown"


# --------------------------------------------------------------------------------------
# narrative generators
# --------------------------------------------------------------------------------------

SYMPTOM_TEMPLATES = [
    "{code} displayed on HMI; {mname} stopped {where}. Andon pulled at {hhmm}.",
    "Operator reports: {desc_lc}. Machine halted in cycle, alarm {code}.",
    "{mname} faulted ({code}). Line lead called maintenance via radio at {hhmm}.",
    "Alarm {code} - {desc_lc}. Downstream {impact}.",
    "At {hhmm} {mname} went down with {code}. Operator tried reset twice, alarm returned.",
    "Intermittent {code} over last hour, now hard-stopped. Operator noted {symptom_extra}.",
]
WHERE = ["mid-cycle", "at part pickup", "during start-up", "at cycle end", "after a die/tool change", "after restart from break"]
IMPACT = ["buffer is draining", "station is starved", "queue is building upstream", "line is blocked", "no immediate impact (buffer ok)"]
SYMPTOM_EXTRA = ["a burning/oil smell", "slower cycle than usual over the shift", "unusual noise", "a small puddle near the base",
                 "warm housing", "reject rate creeping up", "nothing unusual before the stop"]
HANDOFF = ["Handed over to next shift for monitoring.", "Machine returned to production, monitor closely.",
           "Follow-up inspection requested next PM window.", "Spare ordered; temporary fix in place.",
           "Root cause confirmed; permanent fix complete.", "Tested 5 good cycles before release."]


def sensor_snapshot(rng, fam, fault):
    """Sensor readings at the moment of the fault (ground truth signature for the anomaly model)."""
    snap = {}
    sig = fault.get("sig")
    for s in fam["sensors"]:
        val = rng.gauss(s["nominal"], s["sigma"])
        if sig and s["name"] == sig[0]:
            warn, alarm = s["warn"], s["alarm"]
            frac = rng.uniform(0.55, 1.15)
            val = s["nominal"] + (warn - s["nominal"]) * frac if sig[1] != "spike" else s["nominal"] + (alarm - s["nominal"]) * rng.uniform(0.9, 1.3)
            if sig[1] == "decay":
                val = s["nominal"] + (alarm - s["nominal"]) * rng.uniform(0.5, 1.0)
        snap[s["name"]] = round(val, 3 if abs(s["nominal"]) < 1 else 2)
    return snap


def cm_narratives(rng, m, fam, fault, shift, ts, tech_name, down):
    hhmm = ts.strftime("%H:%M")
    desc_lc = lc_first(fault["desc"])
    symptom = rng.choice(SYMPTOM_TEMPLATES).format(
        code=fault["code"], mname=m["name"], desc_lc=desc_lc, where=rng.choice(WHERE), hhmm=hhmm,
        impact=rng.choice(IMPACT), symptom_extra=rng.choice(SYMPTOM_EXTRA))
    causes = fault["causes"]
    cause = causes[min(int(rng.expovariate(1.2)), len(causes) - 1)]
    actions = fault["actions"]
    n_act = rng.randint(max(1, len(actions) - 2), len(actions))
    act_list = actions[:n_act]
    arrive = (ts + dt.timedelta(minutes=rng.randint(2, 15))).strftime("%H:%M")
    reading = ""
    if fault.get("sig"):
        s = next((x for x in fam["sensors"] if x["name"] == fault["sig"][0]), None)
        if s:
            v = s["nominal"] + (s["warn"] - s["nominal"]) * rng.uniform(0.7, 1.2)
            reading = f" Measured {s['name']} = {v:.2f} {s['unit']} (nominal {s['nominal']}, warn {s['warn']}, alarm {s['alarm']})."
    style = rng.random()
    if style < 0.35:
        diag = f"Arrived {arrive}. {past(act_list[0])}.{reading} Cause: {lc_first(cause)}."
        action = "; ".join(past(a) for a in act_list[1:] or act_list) + "."
    elif style < 0.75:
        diag = (f"On site {arrive}. Followed troubleshooting steps in the {m['vendor']} {m['model']} manual for {fault['code']}."
                f"{reading} Found: {lc_first(cause)}.")
        action = " ".join(f"{i + 1}) {past(a)}." for i, a in enumerate(act_list))
    else:
        diag = f"Initial check {arrive}, {m['name']} fault {fault['code']} confirmed.{reading} Probable cause {lc_first(cause)}."
        action = f"{past(act_list[0])}. " + (" ".join(past(a) + "." for a in act_list[1:]) if len(act_list) > 1 else "")
    handoff = rng.choice(HANDOFF)
    notes = f"{handoff} Total downtime {int(down)} min."
    return symptom, diag, action.strip(), cause, notes


def pdm_alert_narrative(rng, fam, sensor, trend_days, value):
    return (f"Condition-based alert: {sensor['name']} trending toward warning threshold over the last {trend_days} days "
            f"(current {value:.2f} {sensor['unit']}; nominal {sensor['nominal']}, warn {sensor['warn']}, alarm {sensor['alarm']}). "
            f"Inspection scheduled before the next planned PM.")


# --------------------------------------------------------------------------------------
# work-order generation
# --------------------------------------------------------------------------------------

CM_BASE_PER_YEAR = {"A": 14, "B": 9, "C": 5}
FAMILY_RATE_MULT = {"TQ": 1.4, "BT": 1.2, "WK": 1.0, "WF": 1.0, "WA": 0.9, "PR": 1.1, "CV": 1.0, "AM": 1.3, "DK": 1.2,
                    "CP": 0.8, "SS": 0.4, "CR": 0.5, "GP": 1.6, "PRS": 1.3, "CNC": 1.0}


def due_dates(rng, m, pm):
    """Generate scheduled PM due dates for the window."""
    if pm["interval_days"]:
        step = pm["interval_days"]
    else:
        step = max(1, int(round(pm["interval_hours"] / m["weekly_hours"] * 7)))
    m_start = max(START, dt.date.fromisoformat(m["commissioned_date"]))
    first = m_start + dt.timedelta(days=rng.randint(0, max(1, min(step, 60))))
    d = first
    out = []
    while d <= END:
        out.append(d)
        d += dt.timedelta(days=step)
    return out, step


PM_FINDINGS = [
    "Minor weep at fitting noted; tightened to spec, monitor.",
    "Cooler fins partially fouled; cleaned.",
    "Cable jacket abrasion found on dress pack; wrapped, replacement planned next window.",
    "Oil sample Fe slightly elevated vs baseline; resample in 4 weeks.",
    "Filter indicator at amber; replaced filter element.",
    "Loose terminal found in cabinet; re-torqued.",
    "Guard sensor misaligned by ~2 mm; realigned and tested.",
    "Lubrication reservoir low; topped up and logged.",
    "Slight backlash increase on wrist axis vs last baseline; added to watch list.",
    "Grease purge showed dark/contaminated grease; extra purge cycle done.",
    "Calibration reading within limits but drifting; schedule recalibration early.",
    "Warning label worn off; replaced.",
]


def generate_work_orders(rng, machines, emps, assignments):
    idx = Index(machines, emps, assignments)
    wos = []
    daily = []
    seq = [0]

    def new_wo(**kw):
        seq[0] += 1
        kw["_k"] = seq[0]
        wos.append(kw)
        return kw

    # ------------------------- Preventive maintenance -------------------------
    pm_wos_by_machine = defaultdict(list)
    for m in machines:
        fam = FAMILY_BY_KEY[m["family"]]
        for pm in fam["pms"]:
            dates, step = due_dates(rng, m, pm)
            for due in dates:
                if pm["interval_days"] == 1:
                    if due.weekday() >= 5:
                        continue
                    sh = pick_weighted(rng, ["A", "B", "C"], [0.34, 0.34, 0.32])
                    ts, _ = sample_dt(rng, due, sh)
                    ok = rng.random() > 0.035
                    tech = idx.who(m["machine_id"], sh, "primary_tech", rng) or idx.who(m["machine_id"], sh, "operator", rng)
                    daily.append(dict(machine_id=m["machine_id"], date=due.isoformat(), shift=sh, check=pm["task"],
                                      performed_by=tech, result="OK" if ok else "FINDING",
                                      note="" if ok else rng.choice(PM_FINDINGS)))
                    continue
                r = rng.random()
                late_days = 0
                status = "completed"
                if r < 0.06:
                    late_days = rng.randint(3, 21)
                elif r < 0.075:
                    status = "deferred"
                elif r < 0.5:
                    late_days = rng.randint(0, 2)
                done_day = due + dt.timedelta(days=late_days)
                if done_day > END:
                    continue
                while done_day.weekday() >= 6:
                    done_day += dt.timedelta(days=1)
                sh = pick_weighted(rng, ["A", "B", "C"], [0.5, 0.35, 0.15])
                ts, _ = sample_dt(rng, done_day, sh)
                tech_id = idx.who(m["machine_id"], sh, "primary_tech", rng)
                lvl_note = ""
                dur = max(5, int(pm["duration_min"] * rng.uniform(0.8, 1.35)))
                steps = pm["steps"] or ["Perform checklist per PM procedure"]
                finding = rng.choice(PM_FINDINGS) if rng.random() < 0.14 else None
                step_lines = [f"[x] {s}" for s in steps]
                parts_used = []
                for pn, desc, cost in pm["parts"]:
                    parts_used.append(dict(part_no=pn, description=desc, qty=1, unit_cost=cost))
                if status == "deferred":
                    narrative = (f"PM deferred: {rng.choice(['machine not available (production priority)', 'parts on order', 'no qualified technician on shift', 'line down for changeover'])}. "
                                 f"Rescheduled.")
                    step_lines = []
                    dur = 0
                    parts_used = []
                else:
                    narrative = f"{pm['task']} completed. " + (f"Findings: {finding}" if finding else "No abnormal findings.")
                    if late_days > 2:
                        narrative += f" Completed {late_days} days after due date."
                w = new_wo(
                    wo_type="PM", priority="P3", machine_id=m["machine_id"], pm_id=pm["id"], title=pm["task"],
                    opened_ts=(dt.datetime.combine(due, dt.time(5, 30))).isoformat(timespec="minutes"),
                    started_ts=ts.isoformat(timespec="minutes"),
                    closed_ts=(ts + dt.timedelta(minutes=dur)).isoformat(timespec="minutes"),
                    due_date=due.isoformat(), status=status, shift=sh, trade=pm["trade"], skill_required=pm["skill"],
                    reported_by="CMMS auto-generated", assigned_tech=tech_id, fault_code=None,
                    symptom=None, diagnosis=None, action_taken="\n".join(step_lines), root_cause=None,
                    root_cause_category=None, parts_used=parts_used, downtime_min=0 if m["area"] != "UTL" else 0,
                    planned_downtime_min=dur if status == "completed" else 0, labor_hours=round(dur / 60 * rng.choice([1, 1, 2]), 2),
                    escalation_level_reached=0, vendor_involved=False, narrative=narrative, follow_up_wo=None,
                    sensor_snapshot=None, lost_vehicles_est=0)
                pm_wos_by_machine[m["machine_id"]].append(w)
                if finding and rng.random() < 0.35:
                    ts2 = ts + dt.timedelta(days=rng.randint(1, 6))
                    if ts2.date() <= END:
                        new_wo(wo_type="INSPECTION", priority="P3", machine_id=m["machine_id"], pm_id=None,
                               title=f"Follow-up on PM finding: {finding[:50]}",
                               opened_ts=ts.isoformat(timespec="minutes"), started_ts=ts2.isoformat(timespec="minutes"),
                               closed_ts=(ts2 + dt.timedelta(minutes=rng.randint(15, 90))).isoformat(timespec="minutes"),
                               due_date=ts2.date().isoformat(), status="completed", shift=shift_of(ts2), trade=pm["trade"],
                               skill_required="L2", reported_by=idx.name(tech_id), assigned_tech=tech_id, fault_code=None,
                               symptom=finding, diagnosis="Inspected per PM follow-up.",
                               action_taken="Corrective action completed; condition normal.", root_cause=None,
                               root_cause_category=None, parts_used=[], downtime_min=0, planned_downtime_min=30,
                               labor_hours=0.75, escalation_level_reached=0, vendor_involved=False,
                               narrative="Follow-up inspection closed.", follow_up_wo=None, sensor_snapshot=None,
                               lost_vehicles_est=0)

    # ------------------------- Corrective maintenance -------------------------
    years = (END - START).days / 365.0
    cm_wos = []
    for m in machines:
        fam = FAMILY_BY_KEY[m["family"]]
        base = CM_BASE_PER_YEAR[m["criticality"]] * FAMILY_RATE_MULT.get(m["family"], 1.0)
        m_years = (END - max(START, dt.date.fromisoformat(m["commissioned_date"]))).days / 365.0
        n_events = max(2, int(rng.gauss(base * m_years, base * m_years * 0.2)))
        faults = fam["faults"]
        events = []
        wdays = working_days(max(START, dt.date.fromisoformat(m["commissioned_date"])), END)
        for _ in range(n_events):
            f = pick_weighted(rng, faults, [x["w"] for x in faults])
            day = rng.choice(wdays)
            # seasonality for thermal faults (Texas summer)
            if "TEMP" in f["code"] or "OVERTEMP" in f["code"]:
                if day.month in (6, 7, 8, 9) or rng.random() < 0.45:
                    pass
                else:
                    day = rng.choice([d for d in wdays if d.month in (6, 7, 8, 9)])
            events.append((f, day))
        if m["machine_id"] in BAD_ACTORS:
            code, per_year, w0, w1 = BAD_ACTORS[m["machine_id"]]
            f = next(x for x in faults if x["code"] == code)
            span = [d for d in wdays if w0 <= d <= w1]
            n_extra = max(2, int(per_year * len(span) / 250))
            # clustered, accelerating towards the end of the window (degradation story)
            for i in range(n_extra):
                pos = (rng.random() ** 0.6)
                events.append((f, span[min(len(span) - 1, int(pos * len(span)))]))
            if w1 >= END:   # live storyline: the machine is still misbehaving in the last 3 weeks
                for _ in range(2):
                    events.append((f, rng.choice(span[-15:])))
        for f, day in events:
            ts, shift = sample_dt(rng, day)
            lo, hi = f["mttr"]
            beta = rng.betavariate(1.2, 3.0)
            down = lo + (hi - lo) * beta
            if f["sev"] >= 4:
                down = max(down, lo * 1.2)
            down = round(down)
            reported_by = idx.who(m["machine_id"], shift, "operator", rng) or idx.who(m["machine_id"], shift, "line_lead", rng)
            primary = idx.who(m["machine_id"], shift, "primary_tech", rng)
            backup = idx.who(m["machine_id"], shift, "backup_tech", rng)
            tech = primary if rng.random() < 0.8 else (backup or primary)
            symptom, diag, action, cause, notes = cm_narratives(rng, m, fam, f, shift, ts, idx.name(tech), down)
            thr = ESCALATION_TEMPLATE[m["criticality"]]
            level = 1
            for lvl, key in enumerate(["L1_tech", "L2_backup", "L3_supervisor", "L4_engineer", "L5_vendor", "L6_plant_mgmt"], start=1):
                if down >= thr[key]:
                    level = lvl
            if f["sev"] >= 4:
                level = max(level, 4)
            vendor_inv = level >= 5 or (f["sev"] >= 3 and rng.random() < 0.15)
            parts_used = []
            if f["parts"] and rng.random() < 0.8:
                for pn, desc, cost in f["parts"]:
                    if rng.random() < 0.85:
                        parts_used.append(dict(part_no=pn, description=desc, qty=rng.choice([1, 1, 1, 2]),
                                               unit_cost=round(cost * rng.uniform(0.95, 1.1), 2)))
            techs_on = rng.choice([1, 1, 2, 2, 3])
            lost = 0.0
            nominal = PLANT["nominal_rate_vph"]
            if m["criticality"] == "A":
                lost = max(0.0, (down - 8) / 60.0 * nominal * rng.uniform(0.5, 1.0))
            elif m["criticality"] == "B":
                lost = max(0.0, (down - 25) / 60.0 * nominal * rng.uniform(0.2, 0.6))
            priority = {1: "P4", 2: "P3", 3: "P2", 4: "P1"}[f["sev"]]
            w = new_wo(
                wo_type="CM", priority=priority, machine_id=m["machine_id"], pm_id=None,
                title=f"{f['code']}: {f['desc']}",
                opened_ts=ts.isoformat(timespec="minutes"),
                started_ts=(ts + dt.timedelta(minutes=rng.randint(2, 15))).isoformat(timespec="minutes"),
                closed_ts=(ts + dt.timedelta(minutes=down + rng.randint(0, 20))).isoformat(timespec="minutes"),
                due_date=ts.date().isoformat(), status="completed", shift=shift, trade=f["trade"],
                skill_required="L3" if f["sev"] >= 3 else "L2", reported_by=idx.name(reported_by), assigned_tech=tech,
                fault_code=f["code"], fault_code_source=f["source"], symptom=symptom, diagnosis=diag, action_taken=action,
                root_cause=cause, root_cause_category=root_cause_category(cause), parts_used=parts_used,
                downtime_min=down, planned_downtime_min=0, labor_hours=round(down / 60 * techs_on, 2),
                escalation_level_reached=level, vendor_involved=vendor_inv, narrative=notes, follow_up_wo=None,
                sensor_snapshot=sensor_snapshot(rng, fam, f), lost_vehicles_est=round(lost, 1))
            cm_wos.append(w)

            # PdM alert before some failures with a sensor signature (supports prediction demo)
            if f.get("sig") and rng.random() < 0.35:
                s = next((x for x in fam["sensors"] if x["name"] == f["sig"][0]), None)
                if s:
                    lead = rng.randint(3, 21)
                    t0 = ts - dt.timedelta(days=lead)
                    if t0.date() >= START and t0.weekday() < 5:
                        val = s["nominal"] + (s["warn"] - s["nominal"]) * rng.uniform(0.6, 0.95)
                        new_wo(wo_type="PdM", priority="P3", machine_id=m["machine_id"], pm_id=None,
                               title=f"Condition alert: {s['name']} trending", opened_ts=t0.isoformat(timespec="minutes"),
                               started_ts=(t0 + dt.timedelta(hours=rng.randint(4, 30))).isoformat(timespec="minutes"),
                               closed_ts=(t0 + dt.timedelta(hours=rng.randint(30, 60))).isoformat(timespec="minutes"),
                               due_date=(t0 + dt.timedelta(days=lead - 1)).date().isoformat(), status="completed",
                               shift=shift_of(t0), trade=f["trade"], skill_required="L2",
                               reported_by="Condition monitoring (auto)", assigned_tech=primary, fault_code=None,
                               symptom=pdm_alert_narrative(rng, fam, s, rng.randint(3, 14), val),
                               diagnosis="Trend confirmed on site; no immediate defect found." if rng.random() < 0.6 else "Early wear signs visible.",
                               action_taken="Increased monitoring frequency; planned corrective work for next PM window.",
                               root_cause=None, root_cause_category=None, parts_used=[], downtime_min=0,
                               planned_downtime_min=20, labor_hours=0.8, escalation_level_reached=0, vendor_involved=False,
                               narrative=f"Linked to later failure {f['code']} on {ts.date().isoformat()}.",
                               follow_up_wo=None, sensor_snapshot=None, lost_vehicles_est=0)

    # ------------------------- sort, ID, link -------------------------
    wos.sort(key=lambda w: (w["opened_ts"], w["_k"]))
    per_year = defaultdict(int)
    for w in wos:
        y = w["opened_ts"][:4]
        per_year[y] += 1
        w["wo_id"] = f"WO-{y}-{per_year[y]:06d}"
        w.pop("_k")
        w.setdefault("fault_code_source", None)
    # follow-up links for repeat failures (same machine+code within 7 days)
    last = {}
    for w in wos:
        if w["wo_type"] != "CM":
            continue
        key = (w["machine_id"], w["fault_code"])
        if key in last:
            prev = last[key]
            if (dt.datetime.fromisoformat(w["opened_ts"]) - dt.datetime.fromisoformat(prev["opened_ts"])).days <= 14:
                prev["follow_up_wo"] = w["wo_id"]
                w["narrative"] += f" Repeat failure within 14 days of {prev['wo_id']}."
        last[key] = w
    return wos, daily


# --------------------------------------------------------------------------------------
# Vendor service logs
# --------------------------------------------------------------------------------------

SERVICE_VISIT_TYPES = [
    ("Annual fleet PM", 1.0), ("Warranty repair", 0.2), ("Emergency callout", 0.6), ("Firmware / software update", 0.5),
    ("Calibration / certification", 0.5), ("Performance audit", 0.2),
]

VENDOR_VISIT_RULES = {
    # vendor -> list of (visit_type, interval_days, families affected = None means all of vendor)
    "KUKA": [("Annual fleet PM", 365), ("Firmware / software update", 540)],
    "FANUC": [("Annual fleet PM", 365), ("Firmware / software update", 540)],
    "ABB": [("Annual fleet PM", 365)],
    "IDRA": [("Semi-annual machine service", 182), ("Hydraulic / injection performance audit", 365)],
    "TRUMPF": [("Semi-annual laser service", 182)],
    "Duerr": [("Annual paint/process service", 365)],
    "Atlas Copco": [("Annual tool calibration & controller update", 365)],
    "Desoutter": [("Annual tool calibration", 365)],
    "ZEISS": [("Annual metrology calibration", 365)],
    "INFICON": [("Annual leak-standard calibration", 365)],
    "Chroma": [("Annual HV tester calibration", 365)],
    "AVL": [("Annual NVH bench calibration", 365)],
    "MAHA": [("Annual dyno calibration", 365)],
    "Siemens": [("Annual breaker & relay service", 365)],
    "Carrier": [("Semi-annual chiller service", 182)],
    "Konecranes": [("Annual crane inspection", 365)],
    "Yxlon": [("Annual X-ray safety & performance check", 365)],
    "DMG MORI": [("Annual geometry service", 365)],
    "Schuler": [("Annual press inspection", 365)],
    "Striko Westofen": [("Annual furnace inspection", 365)],
    "Nordson": [("Annual dispense service", 365)],
    "Aumann": [("Annual line service", 365)],
    "Hunter": [("Annual ADAS target calibration", 365)],
    "MiR": [("Annual AMR service", 365)],
}


def generate_service_logs(rng, machines, wos, emps):
    out = []
    by_vendor = defaultdict(list)
    for m in machines:
        by_vendor[m["vendor"]].append(m)
    seq = [0]

    def add(**kw):
        seq[0] += 1
        kw["service_id"] = f"SVC-{seq[0]:05d}"
        out.append(kw)

    # scheduled visits
    for vendor, rules in VENDOR_VISIT_RULES.items():
        ms = by_vendor.get(vendor, [])
        if not ms:
            continue
        sla = VENDOR_SLA[vendor]
        for vtype, interval in rules:
            d = START + dt.timedelta(days=rng.randint(10, min(interval, 200)))
            while d <= END:
                # one visit per area/vendor group per cycle
                groups = defaultdict(list)
                for m in ms:
                    groups[m["area"]].append(m)
                for area, gm in groups.items():
                    vd = d + dt.timedelta(days=rng.randint(0, 25))
                    if vd > END:
                        continue
                    gm = [x for x in gm if dt.date.fromisoformat(x["commissioned_date"]) <= vd]
                    if not gm:
                        continue
                    while vd.weekday() >= 5:
                        vd += dt.timedelta(days=1)
                    eng = rand_name(rng)
                    t0 = dt.datetime.combine(vd, dt.time(rng.choice([7, 8, 9, 13, 14]), rng.choice([0, 15, 30])))
                    hours = round(rng.uniform(3, 10) * min(3, 1 + len(gm) / 6), 1)
                    findings = rng.sample([
                        "Wear within limits on all inspected components.", "Minor lubrication starvation on two units; corrected.",
                        "Calibration drift found and corrected; certificates issued.",
                        "Recommend replacing consumables at next PM (see parts list).",
                        "Firmware two versions behind; updated to current release with customer approval.",
                        "Safety function validation passed; documented in report.",
                        "Elevated vibration on one unit; condition monitoring recommended.",
                        "Cabinet filters and fans cleaned; no thermal issues.",
                        "Recommend spare critical parts be held on site (see recommendations).",
                    ], k=rng.randint(2, 4))
                    ids = [m["machine_id"] for m in gm[:12]]
                    add(vendor=vendor, machine_ids=ids, area=area, visit_type=vtype, ticket_no=f"{vendor[:3].upper()}-{rng.randint(100000, 999999)}",
                        request_ts=(t0 - dt.timedelta(days=rng.randint(14, 45))).isoformat(timespec="minutes"),
                        onsite_start=t0.isoformat(timespec="minutes"),
                        onsite_end=(t0 + dt.timedelta(hours=hours)).isoformat(timespec="minutes"),
                        response_time_h=None, sla_met=True, engineer=eng, linked_wo_id=None, warranty=False,
                        parts=[], cost_usd=round(hours * rng.uniform(175, 260) + rng.uniform(0, 600), 2),
                        findings=" ".join(findings),
                        actions="Performed scheduled service per OEM maintenance plan; updated service records and left report with maintenance planner.",
                        recommendations=rng.choice(["No action needed.", "Replace worn consumables within 3 months.",
                                                    "Schedule follow-up inspection in 90 days.", "Hold one critical spare on site."]),
                        next_service_due=(vd + dt.timedelta(days=interval)).isoformat())
                d += dt.timedelta(days=interval)

    # emergency callouts linked to CM work orders that reached vendor level
    for w in wos:
        if w["wo_type"] != "CM" or not w["vendor_involved"]:
            continue
        m = next(x for x in machines if x["machine_id"] == w["machine_id"])
        sla = VENDOR_SLA[m["vendor"]]
        t_req = dt.datetime.fromisoformat(w["opened_ts"]) + dt.timedelta(minutes=rng.randint(40, 180))
        resp = rng.uniform(0.2, sla["response_h"] * 1.4)
        onsite_h = rng.uniform(2, sla["onsite_h"] * 1.2)
        t_on = t_req + dt.timedelta(hours=onsite_h)
        dur = rng.uniform(2, 14)
        fam = FAMILY_BY_KEY[m["family"]]
        f = next(x for x in fam["faults"] if x["code"] == w["fault_code"])
        parts = [dict(oem_part_no=f"{m['vendor'][:3].upper()}-{rng.randint(100000, 999999)}", description=p[1], qty=1,
                      warranty=(dt.date.fromisoformat(m["install_date"]) + dt.timedelta(days=730) > t_req.date()),
                      unit_cost=p[2]) for p in f["parts"][:2]]
        warranty = any(p["warranty"] for p in parts) and rng.random() < 0.5
        add(vendor=m["vendor"], machine_ids=[m["machine_id"]], area=m["area"],
            visit_type="Emergency callout", ticket_no=f"{m['vendor'][:3].upper()}-{rng.randint(100000, 999999)}",
            request_ts=t_req.isoformat(timespec="minutes"),
            onsite_start=t_on.isoformat(timespec="minutes"), onsite_end=(t_on + dt.timedelta(hours=dur)).isoformat(timespec="minutes"),
            response_time_h=round(resp, 2), sla_met=(resp <= sla["response_h"] and onsite_h <= sla["onsite_h"]),
            engineer=rand_name(rng), linked_wo_id=w["wo_id"], warranty=warranty, parts=parts,
            cost_usd=0.0 if warranty else round(dur * rng.uniform(190, 280) + sum(p["unit_cost"] for p in parts), 2),
            findings=f"{f['code']} ({f['desc']}). Cause confirmed: {w['root_cause']}.",
            actions=w["action_taken"] if w["action_taken"] else "Repair completed.",
            recommendations=rng.choice(["Add condition monitoring on affected subsystem.", "Replace related wear parts at next PM.",
                                        "Review operating parameters with process engineering.", "No further action."]),
            next_service_due=None)
    out.sort(key=lambda s: s["onsite_start"])
    for i, s in enumerate(out, 1):
        s["service_id"] = f"SVC-{i:05d}"
    return out


# --------------------------------------------------------------------------------------
# Incidents + RCA reports
# --------------------------------------------------------------------------------------

INCIDENT_TYPES = [
    ("Near miss", 0.3), ("First aid", 0.04), ("Quality escape", 0.2), ("Environmental (spill/leak)", 0.1),
    ("Equipment damage", 0.1), ("LOTO deviation", 0.06), ("HV / battery event", 0.04), ("Fire / smoke", 0.02),
    ("Process deviation", 0.14),
]

NEAR_MISS_TEXT = [
    "Operator noticed unguarded pinch point during die change; stopped work and informed supervisor.",
    "Forklift and pedestrian came within 1 m at an intersection near the area; no contact.",
    "Dropped tool from platform during PM; exclusion zone prevented injury.",
    "Technician began work before confirming zero-energy verification; peer caught it, work paused.",
    "Hydraulic hose whipped after fitting failed under pressure; area was clear.",
    "Light curtain muted longer than expected after sequence fault; investigated and corrected.",
]
QUALITY_TEXT = [
    "Torque-NOK vehicles found at audit gate; fastener batch quarantined and re-checked.",
    "Weld nugget undersize on side-frame detected by ultrasonic sample; guns re-dressed and parameters verified.",
    "Paint film thickness low on rear quarter; flow rate drift corrected.",
    "Casting porosity spike flagged by X-ray; die spray and vacuum settings reviewed.",
    "Pack leak test false-fail trend; fixture contacts replaced.",
    "ADAS camera calibration out-of-window on 6 vehicles; target alignment re-verified.",
]
ENV_TEXT = [
    "Hydraulic oil weep at hose fitting; absorbed with pads, no drain contact.",
    "Coolant overflow at CNC sump after filter loaded; contained.",
    "Compressor condensate drain failed and leaked to floor; cleaned.",
    "Paint solvent drip at color changer; cleaned per procedure.",
]


def generate_incidents(rng, machines, wos, emps):
    cms = [w for w in wos if w["wo_type"] == "CM"]
    mm = {m["machine_id"]: m for m in machines}
    inc = []
    rcas = []
    n = 340
    types = [t for t, _ in INCIDENT_TYPES]
    wts = [w for _, w in INCIDENT_TYPES]
    ehs = [e for e in emps if e["role_code"] in ("EHS", "QAE", "ARM", "MSV")]
    for i in range(n):
        t = pick_weighted(rng, types, wts)
        m = rng.choice(machines)
        day = rng.choice(working_days(max(START, dt.date.fromisoformat(m["commissioned_date"])), END))
        ts, shift = sample_dt(rng, day)
        owner = rng.choice(ehs)["name"]
        if t == "Near miss":
            desc = rng.choice(NEAR_MISS_TEXT)
            sev = "Low"
        elif t == "Quality escape":
            desc = rng.choice(QUALITY_TEXT); sev = rng.choice(["Low", "Medium", "Medium", "High"])
        elif t.startswith("Environmental"):
            desc = rng.choice(ENV_TEXT); sev = "Low"
        elif t == "First aid":
            desc = rng.choice(["Minor cut on hand during tool handling; first aid applied on site.",
                               "Eye irritation from cleaning agent; eyewash used, returned to work."]); sev = "Low"
        elif t == "HV / battery event":
            desc = rng.choice(["Insulation fault alarm on pack test; pack quarantined and HV safety engineer notified.",
                               "Pack cell voltage deviation flagged on EOL test; held for teardown analysis."]); sev = "High"
        elif t == "Fire / smoke":
            desc = rng.choice(["Smoke from overheated motor terminal box; E-stop and fire watch; no spread.",
                               "Burnt smell and smoke at conveyor drive; breaker tripped, area cleared."]); sev = "High"
        elif t == "LOTO deviation":
            desc = "Lock applied without full try-out verification; supervisor audit caught the gap."; sev = "Medium"
        elif t == "Equipment damage":
            desc = rng.choice(["Forklift struck conveyor guard; guard replaced.", "Robot tooling collision damaged fixture; replaced."]); sev = "Medium"
        else:
            desc = "Process parameter outside approved window during shift; corrected and reviewed."; sev = "Low"
        inc.append(dict(incident_id=f"INC-{i + 1:04d}", date=ts.date().isoformat(), time=ts.strftime("%H:%M"), shift=shift,
                        type=t, severity=sev, area=m["area"], machine_id=m["machine_id"], description=desc,
                        immediate_action="Area secured, supervisor and EHS informed; corrective steps started.",
                        root_cause=rng.choice(["Procedure not followed", "Inadequate guarding", "Wear / aging", "Training gap",
                                               "Parameter drift", "Material variation", "Housekeeping", "Design limitation"]),
                        corrective_actions=rng.choice(["Retrained operators and updated SOP.", "Installed additional guarding.",
                                                       "Added inspection step to PM.", "Adjusted parameters and added alert.",
                                                       "Replaced component and increased PM frequency."]),
                        owner=owner, status=rng.choice(["Closed", "Closed", "Closed", "Open - action in progress"]),
                        linked_wo=None))
    inc.sort(key=lambda x: (x["date"], x["time"]))
    for i, x in enumerate(inc, 1):
        x["incident_id"] = f"INC-{i:04d}"

    # RCA reports for long downtime events
    big = sorted([w for w in cms if w["downtime_min"] >= 240], key=lambda w: -w["downtime_min"])[:60]
    for k, w in enumerate(sorted(big, key=lambda x: x["opened_ts"]), 1):
        m = mm[w["machine_id"]]
        rid = f"RCA-{k:03d}"
        text = f"""# {rid}: {w['title']}

**Machine:** {m['machine_id']} ({m['name']}, {m['vendor']} {m['model']}) - Area: {m['area_name']}
**Date:** {w['opened_ts'][:10]}  **Shift:** {w['shift']}  **Downtime:** {w['downtime_min']} min  **Estimated lost vehicles:** {w['lost_vehicles_est']}
**Work order:** {w['wo_id']}  **Escalation level reached:** L{w['escalation_level_reached']}

## Problem statement
{w['symptom']}

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor {m['vendor']} was {'engaged' if w['vendor_involved'] else 'not required'}.

## Investigation
{w['diagnosis']}

## Root cause
{w['root_cause']} (category: {w['root_cause_category']}).

## Corrective actions taken
{w['action_taken']}

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor ({rng.choice(['vibration', 'temperature', 'current', 'pressure'])}) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: {rng.choice(emps)['name']}  Due: {(dt.date.fromisoformat(w['opened_ts'][:10]) + dt.timedelta(days=rng.randint(14, 45))).isoformat()}
"""
        rcas.append(dict(rca_id=rid, wo_id=w["wo_id"], machine_id=w["machine_id"], date=w["opened_ts"][:10], text=text))
    return inc, rcas


# --------------------------------------------------------------------------------------
# Handover notes
# --------------------------------------------------------------------------------------

def generate_handover_notes(rng, machines, wos, emps, days=120):
    start = END - dt.timedelta(days=days)
    by_area_shift_day = defaultdict(list)
    mm = {m["machine_id"]: m for m in machines}
    for w in wos:
        if w["wo_type"] != "CM":
            continue
        d = dt.date.fromisoformat(w["opened_ts"][:10])
        if d < start:
            continue
        by_area_shift_day[(mm[w["machine_id"]]["area"], w["shift"], d)].append(w)
    psv = defaultdict(list)
    for e in emps:
        if e["role_code"] == "PSV":
            psv[(e["area"], e["shift"])].append(e)
    notes = []
    for d in working_days(start, END):
        for area in AREAS:
            for sh in "ABC":
                evs = by_area_shift_day.get((area, sh, d), [])
                sup = psv[(area, sh)][0]["name"] if psv.get((area, sh)) else "N/A"
                plan = max(0, int(rng.gauss(PLANT["nominal_rate_vph"] * 8 * 0.92, 18))) if area in ("BIW", "PNT", "GA", "EOL", "BAT", "DRV") else None
                lost = sum(w["lost_vehicles_est"] for w in evs)
                prod = int(plan - lost) if plan else None
                text = f"{AREAS[area]['name']} - Shift {sh} handover ({d.isoformat()}), supervisor {sup}. "
                if prod is not None:
                    text += f"Output {prod} units vs plan {plan}. "
                if evs:
                    parts = []
                    for w in evs[:4]:
                        parts.append(f"{w['machine_id']} {w['fault_code']} ({w['downtime_min']} min, {w['wo_id']})")
                    text += "Downtime events: " + "; ".join(parts) + ". "
                    if any(w["escalation_level_reached"] >= 5 for w in evs):
                        text += "Vendor support was engaged on at least one event; follow-up expected next shift. "
                else:
                    text += "No unplanned downtime. "
                text += rng.choice(["Housekeeping good.", "Watch hydraulic temperatures this week.", "Spare consumables low, request raised.",
                                    "No safety issues.", "One near miss reported; see EHS log.", "Training sessions on SOP refresh in progress.",
                                    "Next shift: continue monitoring recently repaired equipment."])
                notes.append(dict(date=d.isoformat(), area=area, shift=sh, supervisor=sup, units=prod, plan=plan,
                                  downtime_events=[w["wo_id"] for w in evs], text=text))
    return notes


# --------------------------------------------------------------------------------------
# Spare parts inventory
# --------------------------------------------------------------------------------------

def generate_spare_parts(rng, wos):
    seen = {}
    for fam in FAMILIES:
        for f in fam["faults"]:
            for pn, desc, cost in f["parts"]:
                seen.setdefault(pn, dict(part_no=pn, description=desc, unit_cost=cost, vendors=set(), families=set()))
                seen[pn]["vendors"].add(fam["vendor"]); seen[pn]["families"].add(fam["key"])
        for pm in fam["pms"]:
            for pn, desc, cost in pm["parts"]:
                seen.setdefault(pn, dict(part_no=pn, description=desc, unit_cost=cost, vendors=set(), families=set()))
                seen[pn]["vendors"].add(fam["vendor"]); seen[pn]["families"].add(fam["key"])
    usage = defaultdict(int)
    for w in wos:
        for p in w["parts_used"]:
            usage[p["part_no"]] += p["qty"]
    rows = []
    for pn, p in seen.items():
        years = (END - START).days / 365
        yearly = usage[pn] / years
        crit = p["unit_cost"] > 1500
        lead = rng.choice([7, 14, 21]) if not crit else rng.choice([35, 56, 84, 126])
        minq = max(1, int(math.ceil(yearly * lead / 365 * 1.5)))
        rows.append(dict(part_no=pn, description=p["description"], unit_cost_usd=p["unit_cost"],
                         vendors="/".join(sorted(p["vendors"])), families="/".join(sorted(p["families"])),
                         annual_usage=round(yearly, 1), min_stock=minq, on_hand=max(0, int(rng.gauss(minq * 1.3, minq * 0.8))),
                         lead_time_days=lead, bin_location=f"{rng.choice(['MS1', 'MS2', 'LINE'])}-{rng.choice('ABCDEF')}{rng.randint(1, 40):02d}",
                         critical_spare=crit))
    return rows
