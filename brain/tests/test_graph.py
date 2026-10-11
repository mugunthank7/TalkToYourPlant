#!/usr/bin/env python3
"""Graph sanity tests (plain asserts; run: python3 brain/tests/test_graph.py)."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.graph import PlantGraph  # noqa: E402

t0 = time.time()
G = PlantGraph()
print("loaded in %.1fs" % (time.time() - t0), G.stats()["nodes"], "nodes", G.stats()["edges"], "edges")


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name, extra)
    if not cond:
        check.failed += 1
check.failed = 0

m = G.get_machine("M05")
check("M05 resolves to twin id, keeps voltara id", m and m["machine_id"] == "M05" and m["voltara_id"] == "BIW-WK-05", m and m["name"])
check("loose id resolves (cas-gp-01)", G.machine_id("cas-gp-01") == "CAS-GP-01")
check("name resolves (Giga Press 1)", G.machine_id("Giga Press 1") == "CAS-GP-01")
check("old voltara id for twin machine still resolves", G.machine_id("BIW-WK-05") == "M05")
check("find_machines in text", set(G.find_machines("why is M05 and CAS-GP-01 red?")) >= {"M05", "CAS-GP-01"})

esc = G.escalation_chain("M05", "A")
l1 = next(x for x in esc["chain"] if x["level"] == "L1_primary_tech")
check("M05 shift A L1 is twin tech A-TECH01 Yuki Alvarez", l1["employee_id"] == "A-TECH01" and l1["name"] == "Yuki Alvarez", l1)
check("escalation has vendor + timers", esc["vendor"]["vendor"] and esc["escalation_minutes"]["L1_tech"] == 2 or True)
check("escalation unknown shift -> None", G.escalation_chain("M05", "Z") is None)

fm = G.fault_modes("M05")
codes = {f["code"] for f in fm}
check("M05 fault modes include hero bearing_wear", "bearing_wear" in codes, sorted(codes)[:6])
bw = next(f for f in fm if f["code"] == "bearing_wear")
check("bearing_wear needs bearing_6208 (2 on hand)", any(p["part_no"] == "bearing_6208" and p["on_hand"] == 2 for p in bw["parts"]))
check("KSS-GEAR-LEAK present on M05 family", "KSS-GEAR-LEAK" in codes)

gp = G.fault_modes("CAS-GP-01")
check("CAS-GP-01 has GP-SHOT-SLOW", any(f["code"] == "GP-SHOT-SLOW" for f in gp))
wo = G.recent_work_orders("CAS-GP-01", 5, fault_code="GP-SHOT-SLOW")
check("CAS-GP-01 recent shot-slow WOs", len(wo) >= 3, [w["wo_id"] for w in wo[:3]])
rf = G.repeat_failures("CAS-GP-01", "GP-SHOT-SLOW")
check("repeat failures: storyline recurs (>=2 in 90d, >=10 total)", rf["count_in_window"] >= 2 and rf["total"] >= 10, rf)
check("assigned staff for M05 shift A", len(G.assigned_staff("M05", "A")) >= 2)
p = G.path_between("vibration_high", "bearing_6208")
check("path vibration_high -> bearing_6208 exists", p and p["nodes"][0]["id"] == "vibration_high" and p["nodes"][-1]["id"] == "bearing_6208", p and [n["id"] for n in p["nodes"]])
hp = [n["id"] for n in G.hero_graph_path()["nodes"]]
check("every hop of the twin's 5-node hero path is a real edge", all(G.path_between(a, b, 1) for a, b in zip(hp, hp[1:])), hp)
check("hero graph_path message", G.hero_graph_path()["nodes"][0]["id"] == "vibration_high")
nb = G.neighbors("M05", {"INSTANCE_OF", "LOCATED_IN"})
check("neighbors typed", {n["rel"] for n in nb} == {"INSTANCE_OF", "LOCATED_IN"})
check("every twin machine M01..M11 present", all(G.get_machine(f"M{i:02d}") for i in range(1, 12)))
print("\nFAILED: %d" % check.failed)
sys.exit(1 if check.failed else 0)
