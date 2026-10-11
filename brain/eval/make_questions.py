#!/usr/bin/env python3
"""Generate eval/questions.jsonl with gold answers drawn from the actual data (deterministic)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.graph import PlantGraph  # noqa: E402

G = PlantGraph()
Q = []


def add(cat, question, machine=None, gold_sources=(), must=(), tools=(), highlight=(), action=None, cite=False, ref=""):
    Q.append({"id": f"Q{len(Q)+1:02d}", "category": cat, "question": question, "machine": machine,
              "gold_sources": list(gold_sources), "must_include": [list(m) for m in must],
              "expect_tools": list(tools), "expect_highlight": list(highlight),
              "expect_action": action, "expect_citation": cite, "reference": ref})


def l1(mid, shift):
    e = G.escalation_chain(mid, shift)
    return next(x for x in e["chain"] if x["level"] == "L1_primary_tech")["name"]


# 1. who to page (8)
for mid, sh in [("M05", "A"), ("M01", "B"), ("CAS-GP-01", "A"), ("PNT-PR-04", "C"), ("BAT-BL-01", "B"),
                ("BIW-WK-03", "A"), ("UTL-CP-02", "C"), ("GA-TQ-07", "B")]:
    e = G.escalation_chain(mid, sh)
    names = {x["level"]: x["name"] for x in e["chain"]}
    add("who_to_page", f"Who do I page for {mid} on shift {sh}?", mid, [f"{mid}-{sh}"], [[l1(mid, sh)]],
        ["escalation_chain"], [mid], cite=True,
        ref=f"On shift {sh} page the L1 primary technician {names['L1_primary_tech']} first, then the L2 backup technician "
            f"{names['L2_backup_tech']}, then the L3 maintenance supervisor {names['L3_maintenance_supervisor']}.")

# 2. fault-code meaning (6)
for code, mid, fam, kw in [("SRVO-062", "M04", "WF", ["pulsecoder", "absolute position"]),
                           ("KSS-GEAR-LEAK", "BIW-WK-03", "WK", ["oil", "seal"]),
                           ("GP-SHOT-SLOW", "CAS-GP-01", "GP", ["shot", "speed"]),
                           ("TQ-NOK", "GA-TQ-07", "TQ", ["torque", "window"]),
                           ("LSR-PWR-LOW", "BAT-BL-01", "BL", ["laser", "power"]),
                           ("CMP-DISCH-TEMP", "UTL-CP-02", "CP", ["discharge", "temperature"])]:
    desc = next(x["description"] for f in G.fault_modes(mid) if f["code"] == code for x in [f])
    add("fault_code", f"What does fault code {code} mean on {mid}?", mid, [f"MAN-{fam}"], [kw], highlight=[mid], cite=True,
        ref=f"Fault code {code} means: {desc}.")

# 3. which SOP (5)
for q, sop, kw in [("Which SOP covers lockout tagout?", "SOP-SAF-01", ["lockout"]),
                   ("What is the fault escalation and paging protocol SOP?", "SOP-MNT-01", ["escalation"]),
                   ("Which procedure covers FANUC backup battery alarms SRVO-062 and SRVO-065?", "SOP-ROB-02", ["battery"]),
                   ("Which SOP handles torque NOK and tool calibration in general assembly?", "SOP-QA-01", ["torque"]),
                   ("Which SOP covers safe work on the high-voltage EV battery?", "SOP-SAF-02", ["high"])]:
    add("sop", q, None, [sop], [[sop]], ["search_docs"], cite=True, ref=f"{sop} covers this topic.")

# 4. parts (5)
for q, mid, part in [("What spare part is needed to fix KSS-GEAR-LEAK on BIW-WK-03?", "BIW-WK-03", "KUKA-SEAL-A2"),
                     ("Which part does SRVO-065 on M04 need?", "M04", "FAN-A02B-0200-K102"),
                     ("What part do we replace for LSR-PWR-LOW on BAT-BL-01?", "BAT-BL-01", "LSR-PROT-GLASS"),
                     ("Which part is needed for GP-SHOT-SLOW on CAS-GP-01?", "CAS-GP-01", "GP-PLUNGER-TIP"),
                     ("What spare part do we need for the M05 bearing wear and how many are in stock?", "M05", "bearing_6208")]:
    add("parts", q, mid, [], [[part]], ["graph_lookup"], [mid],
        ref=f"The spare part needed is {part}." + (" 2 are in stock." if part == "bearing_6208" else ""))

# 5. repeat failure (4), counts from data
for mid, code in [("CAS-GP-01", "GP-SHOT-SLOW"), ("PNT-PR-04", "PR-BELL-SPEED"), ("BAT-BL-01", "LSR-PWR-LOW"),
                  ("UTL-CP-02", "CMP-DISCH-TEMP")]:
    r = G.repeat_failures(mid, code, 90)
    add("repeat_failure", f"How many times has {mid} had {code} in the last 90 days?", mid, [], [[str(r["count_in_window"])]],
        ["graph_lookup"], [mid],
        ref=f"{mid} had {code} {r['count_in_window']} times in the last {r['window_days']} days.")

# 6. keep running (3)
for h in (2, 0.5, 4):
    add("keep_running", f"M05 is vibrating high. Can we keep running {h} more hours?", "M05", ["SOP-OPS-02"],
        [["SOP-OPS-02"]], ["run_scenario"], ["M05"], cite=True,
        ref="M05 shows bearing wear with about 53 minutes of remaining useful life. Under SOP-OPS-02 a rising warn-level trend "
            "on a criticality A machine limits any extension to the current batch; running longer risks seizure and a long unplanned stop.")

# 7. live storylines (6)
for mid, kw in [("CAS-GP-01", ["shot"]), ("PNT-PR-04", ["bell", "atomizer"]), ("BAT-BL-01", ["laser"]),
                ("BIW-WK-03", ["oil", "leak"]), ("UTL-CP-02", ["discharge"]), ("GA-TQ-07", ["torque"])]:
    add("storyline", f"What is wrong with {mid} and what should we do?", mid, [], [kw], ["get_sensor_state"], [mid],
        ref=f"{mid} has an ongoing fault involving: {', '.join(kw)}. Follow the machine manual, check recent work orders and escalate per the shift chain.")

# 8. hero demo path (3)
add("hero", "Why is M05 red?", "M05", ["SOP-MNT-M05-01"], [["bearing"]], ["get_sensor_state"], ["M05"], cite=True,
    ref="M05 shows rising vibration and temperature from joint 1 bearing wear. The fix is replacing the axis 1 joint bearing with part bearing_6208 following SOP-MNT-M05-01.")
add("hero", "M05 has a bearing problem. Is the spare part in stock?", "M05", [], [["6208"], ["2"]], ["graph_lookup"], ["M05"],
    ref="The spare part is bearing_6208, a deep groove ball bearing 6208. 2 are on hand in the spare parts cage S12.")
add("hero", "Create a work order for the M05 bearing replacement.", "M05", [], [["WO-"]], ["create_work_order"], ["M05"], action="create_work_order",
    ref="A corrective work order is created for M05 component m05_joint1_bearing with spare part bearing_6208.")

out = Path(__file__).resolve().parent / "questions.jsonl"
out.write_text("".join(json.dumps(q) + "\n" for q in Q))
print(len(Q), "questions ->", out)
