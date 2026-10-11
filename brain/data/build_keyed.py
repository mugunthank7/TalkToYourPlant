#!/usr/bin/env python3
"""Build the T-side (brain) dataset keyed to the twin's IDs.

1. Run the Voltara generator (voltara_gen/) into a temp dir.
2. Re-key the mapped machines/employees to the twin IDs (M01..M11, A-TECH01...)
   using crosswalk_*.csv. Unmapped machines keep their Voltara IDs.
3. Add the two gap machines (M03, M10) and the hero M05 bearing-wear content.
4. Write everything to out/ and run integrity checks.

Usage: python3 build_keyed.py [--seed 42] [--out out]
Deterministic. Standard library only.
"""
import argparse, csv, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "voltara_gen"
TEXT_EXT = {".csv", ".json", ".jsonl", ".md"}


def read_csv(p):
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def write_csv(p, rows, fields):
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_jsonl(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def write_jsonl(p, rows):
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def run_generator(seed, raw):
    subprocess.run([sys.executable, "generate.py", "--out", str(raw), "--seed", str(seed)],
                   cwd=GEN, check=True, stdout=subprocess.DEVNULL)


def build_replacements(raw):
    """Ordered (old, new) string pairs: IDs, then display names."""
    machines = {r["machine_id"]: r for r in read_csv(raw / "master/machines.csv")}
    pairs, mapped = [], {}
    for r in read_csv(HERE / "crosswalk_machines.csv"):
        if not r["voltara_id"]:
            continue
        v = machines[r["voltara_id"]]
        mapped[r["voltara_id"]] = r["twin_id"]
        pairs.append((v["name"], r["twin_name"]))        # display name
        pairs.append((r["voltara_id"], r["twin_id"]))    # id
    employees = {r["employee_id"]: r for r in read_csv(raw / "master/employees.csv")}
    esc = {m["machine_id"]: m for m in json.load(open(raw / "master/escalation_matrix.json"))}
    emp_map = {}
    for r in read_csv(HERE / "crosswalk_employees.csv"):
        chain = esc[r["chain_machine"]]["on_shift_chain"][r["shift"]]
        if r["voltara_role_in_chain"] == "L0_production_supervisor":
            # production supervisor is in machine_assignments, not the escalation chain
            vid = None
            for a in read_csv(raw / "master/machine_assignments.csv"):
                if (a["machine_id"] == r["chain_machine"] and a["shift"] == r["shift"]
                        and a["role"] == "production_supervisor"):
                    vid = a["employee_id"]
        else:
            vid = chain[r["voltara_role_in_chain"]]
        emp_map[vid] = r
        old = employees[vid]
        pairs.append((old["name"], r["twin_name"]))
        pairs.append((old["email"], r["twin_name"].lower().replace(" ", ".") + "@voltara-motors.example"))
        pairs.append((vid, r["twin_id"]))
    return pairs, mapped, emp_map


def apply_pairs(text, compiled):
    for rx, new in compiled:
        text = rx.sub(new, text)
    return text


def rekey(raw, out):
    pairs, mapped, emp_map = build_replacements(raw)
    compiled = [(re.compile(r"(?<![A-Za-z0-9_-])" + re.escape(o) + r"(?![A-Za-z0-9_])(?!-\d)"), n)
                for o, n in pairs]
    for p in raw.rglob("*"):
        if p.is_dir():
            continue
        dst = out / p.relative_to(raw)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix in TEXT_EXT:
            dst.write_text(apply_pairs(p.read_text(), compiled))
        else:
            shutil.copy2(p, dst)
    return mapped, emp_map


# ---------------- hero M05 + gap machines (all synthetic) ----------------

HERO_COMPONENTS = [
    ("m05_base", "Base plinth"), ("m05_joint1_bearing", "Axis 1 joint bearing"),
    ("m05_joint2_bearing", "Axis 2 joint bearing"), ("m05_joint3_bearing", "Axis 3 joint bearing"),
    ("m05_servo_motor", "Servo motor"), ("m05_gearbox", "Gearbox"), ("m05_wrist", "Wrist"),
    ("m05_weld_gun", "Spot-weld gun"), ("m05_cable_harness", "Cable harness"),
    ("m05_controller_cabinet", "Controller cabinet"),
]

HERO_SOP = """# SOP-MNT-M05-01: Weld robot axis 1 joint bearing wear: diagnosis and replacement

**Area:** BIW (twin station S06)  |  **Machine:** M05 Weld robot 2  |  **Owner:** Maintenance Supervisor  |  **Revision:** A  |  **Effective:** 2026-10-01

> **Synthetic training document** for the Voltara/Voltline digital-twin demo. Values tagged `synthetic` are invented. Not an OEM document.

## Symptom pattern
- `vibration_rms` rises steadily over hours, with energy in the bearing defect band growing faster than overall RMS.
- `temperature_c` (axis 1 housing) climbs 10 to 15 C above baseline; `motor_current_a` rises about 10 to 15 percent under the same weld cycle.
- Cycle time slips and weld position quality can degrade as play grows.

## Likely cause (failure mode: bearing_wear)
Lubricant breakdown or contamination at the axis 1 joint bearing (`m05_joint1_bearing`), often after a collision event or a missed regrease interval. Left running, wear accelerates and can seize the joint (long unplanned stop).

## Decision: keep running?
Apply SOP-OPS-02. For M05 (criticality A) with vibration above 2x baseline and a rising trend, do not extend beyond the current batch. Plan the bearing change at the next buffer-protected stop.

## Replacement procedure (synthetic)
1. Notify line lead and maintenance bay (S10). Raise a corrective work order for `m05_joint1_bearing`.
2. Pick spare part `bearing_6208` (Deep groove ball bearing 6208, A1 joint) from the spare parts cage (S12). Confirm stock and bin.
3. Lockout/tagout per SOP-SAF-01. Move robot to the service pose and support the arm.
4. Remove axis 1 cover, inspect for metal particles and contamination, take a photo for the work order.
5. Press out the worn bearing, clean the seat, fit the new bearing, regrease with the specified grease.
6. Reassemble, remove LOTO, run a dry cycle, then weld cycles at reduced speed for 10 cycles.
7. Confirm vibration and current back within 10 percent of baseline; close the work order and note the bearing hours.

## Time and parts (synthetic)
- Typical repair time: 90 to 150 minutes (planned) once the part is at the machine.
- Crew: 1 technician plus 1 assistant. Spare stock: 2 on hand, lead time 9 days.

## Escalation
Follow the M05 on-shift chain in the escalation matrix (L1 primary tech, L2 backup, L3 maintenance supervisor).
"""

HERO_PAST_INCIDENT = (
    "Past incident (synthetic): on M04 Weld robot 1, axis 1 joint bearing vibration trended up over "
    "two shifts. The robot was run on for 3 hours past the first alert; the bearing seized and the "
    "line stopped for 4h 20m while the bearing was changed. Lesson: act on the first alert for "
    "bearing wear instead of extending the run. Reference SOP-OPS-02 and SOP-MNT-M05-01."
)

ALERT_M05 = {
    "type": "alert", "machine_id": "M05", "severity": "warning", "score": 0.93,
    "contributors": [{"signal": "vibration_rms", "shap": 0.61},
                     {"signal": "temperature_c", "shap": 0.22},
                     {"signal": "motor_current_a", "shap": 0.10}],
    "component_id": "m05_joint1_bearing",
}
GRAPH_PATH_M05 = {
    "type": "graph_path",
    "nodes": [
        {"id": "vibration_high", "kind": "symptom"},
        {"id": "bearing_wear", "kind": "failure_mode"},
        {"id": "m05_joint1_bearing", "kind": "component"},
        {"id": "replace_bearing", "kind": "repair"},
        {"id": "bearing_6208", "kind": "spare_part"},
    ],
}


def add_hero_and_gaps(out):
    nodes = read_jsonl(out / "rag/graph_nodes.jsonl")
    edges = read_jsonl(out / "rag/graph_edges.jsonl")
    chunks = read_jsonl(out / "rag/rag_chunks.jsonl")
    n_chunk = len(chunks)

    def add_chunk(source_type, source_id, machine_id, title, text, meta=None):
        nonlocal n_chunk
        n_chunk += 1
        chunks.append({"chunk_id": f"h{n_chunk:07d}", "source_type": source_type,
                       "source_id": source_id, "machine_id": machine_id, "area": "BIW",
                       "title": title, "text": text,
                       "metadata": {"source": "synthetic", "origin": "hero_m05", **(meta or {})}})

    # --- graph: contract path nodes (ids match the twin interface contract)
    nodes += [
        {"id": "vibration_high", "label": "Symptom", "kind": "symptom", "name": "High vibration (rms)"},
        {"id": "bearing_wear", "label": "FaultMode", "kind": "failure_mode", "name": "Joint bearing wear",
         "family": "WK", "source": "synthetic"},
        {"id": "replace_bearing", "label": "Repair", "kind": "repair", "name": "Replace axis 1 joint bearing",
         "mttr_min": [90, 150], "source": "synthetic"},
        {"id": "bearing_6208", "label": "Part", "kind": "spare_part",
         "name": "Deep groove ball bearing 6208 (A1 joint)", "on_hand": 2, "lead_time_days": 9,
         "location": "S12", "source": "synthetic"},
        {"id": "SOP-MNT-M05-01", "label": "Document", "name": "Weld robot axis 1 joint bearing wear",
         "source": "synthetic"},
    ]
    for i, cause in enumerate(["Lubricant breakdown or missed regrease interval", "Contamination at the axis 1 joint",
                               "Collision or overload event"]):
        cid_ = f"CAUSE:bearing-wear-{i+1}"
        nodes.append({"id": cid_, "label": "Cause", "text": cause, "source": "synthetic"})
        edges.append({"source": "bearing_wear", "rel": "CAUSED_BY", "target": cid_})
    for cid, name in HERO_COMPONENTS:
        nodes.append({"id": cid, "label": "Component", "kind": "component", "name": name, "machine_id": "M05"})
        edges.append({"source": cid, "rel": "PART_OF", "target": "MACHINE:M05"})
    edges += [
        {"source": "vibration_high", "rel": "INDICATES", "target": "bearing_wear"},
        {"source": "bearing_wear", "rel": "AFFECTS", "target": "m05_joint1_bearing"},
        {"source": "m05_joint1_bearing", "rel": "REPAIRED_BY", "target": "replace_bearing"},
        {"source": "replace_bearing", "rel": "REQUIRES", "target": "bearing_6208"},
        {"source": "FAMILY:WK", "rel": "HAS_FAULT_MODE", "target": "bearing_wear"},
        {"source": "bearing_wear", "rel": "NEEDS_PART", "target": "bearing_6208"},
        {"source": "bearing_wear", "rel": "SHOWS_IN", "target": "vibration_rms"},
        {"source": "bearing_wear", "rel": "DOCUMENTED_IN", "target": "SOP-MNT-M05-01"},
        {"source": "SOP-MNT-M05-01", "rel": "APPLIES_TO", "target": "MACHINE:M05"},
    ]
    # twin signal names as sensor nodes
    for s in ("vibration_rms", "temperature_c", "motor_current_a"):
        nodes.append({"id": s, "label": "SensorChannel", "name": s, "source": "twin_contract"})
        edges.append({"source": "MACHINE:M05", "rel": "HAS_SENSOR", "target": s})

    # --- docs + chunks
    (out / "docs/sops").mkdir(parents=True, exist_ok=True)
    (out / "docs/sops/SOP-MNT-M05-01.md").write_text(HERO_SOP)
    for i, sec in enumerate(re.split(r"\n(?=## )", HERO_SOP)):
        title = sec.strip().splitlines()[0].lstrip("# ").strip()
        label = title if title.startswith("SOP-") else f"SOP-MNT-M05-01: {title}"
        add_chunk("sop", "SOP-MNT-M05-01", "M05", label, f"[{label}]\n{sec.strip()}")
    add_chunk("incident", "INC-HERO-M04", "M04", "Past bearing seizure on Weld robot 1", HERO_PAST_INCIDENT)
    add_chunk("machine_profile", "M05", "M05", "M05 Weld robot 2 hero state",
              "M05 Weld robot 2 (station S06, KUKA KR 210 spot-weld robot, criticality A). "
              "Hero scenario: axis 1 joint bearing (m05_joint1_bearing) develops wear. Symptom path: "
              "vibration_high -> bearing_wear -> m05_joint1_bearing -> replace_bearing -> bearing_6208. "
              "Spare bearing_6208: 2 on hand in spare parts cage S12, lead time 9 days. "
              "Run-extension decisions follow SOP-OPS-02; repair follows SOP-MNT-M05-01.")

    # --- spare part row
    sp_path = out / "master/spare_parts.csv"
    sp = read_csv(sp_path)
    fields = list(sp[0].keys())
    sp.append({"part_no": "bearing_6208", "description": "Deep groove ball bearing 6208 (A1 joint)",
               "unit_cost_usd": "38.0", "vendors": "generic", "families": "WK", "annual_usage": "2.0",
               "min_stock": "1", "on_hand": "2", "lead_time_days": "9", "bin_location": "S12-A3",
               "critical_spare": "True"})
    write_csv(sp_path, sp, fields)

    # --- gap machines M03, M10 (synthetic stubs)
    gaps = [("M03", "Framing fixture", "S04", "BIW", "FIX", "Clamps underbody parts for tack welding"),
            ("M10", "Decoiler", "S01", "STP", "DEC", "Uncoils steel/aluminium coil and feeds the blanking line")]
    mpath = out / "master/machines.csv"
    mrows = read_csv(mpath)
    mfields = list(mrows[0].keys())
    for mid, name, st, area, fam, desc in gaps:
        row = {k: "" for k in mfields}
        row.update({"machine_id": mid, "family": fam, "area": area, "name": name,
                    "criticality": "B", "description": desc + " (synthetic stub for the twin)"})
        mrows.append(row)
        nodes.append({"id": f"MACHINE:{mid}", "label": "Machine", "machine_id": mid, "name": name,
                      "criticality": "B", "source": "synthetic"})
        edges.append({"source": f"MACHINE:{mid}", "rel": "LOCATED_IN", "target": f"AREA:{area}"})
        add_chunk("machine_profile", mid, mid, f"{mid} {name} profile",
                  f"{mid} {name} at station {st}. {desc}. Synthetic stub: no manual or fault history.")
    write_csv(mpath, mrows, mfields)

    # twin metadata on machines.csv
    cw = {r["twin_id"]: r for r in read_csv(HERE / "crosswalk_machines.csv")}
    mrows = read_csv(mpath)
    for r in mrows:
        c = cw.get(r["machine_id"])
        r["voltara_id"] = c["voltara_id"] if c else r["machine_id"]
        r["twin_station"] = c["twin_station"] if c else ""
    write_csv(mpath, mrows, mfields + ["voltara_id", "twin_station"])

    write_jsonl(out / "rag/graph_nodes.jsonl", nodes)
    write_jsonl(out / "rag/graph_edges.jsonl", edges)
    write_jsonl(out / "rag/rag_chunks.jsonl", chunks)
    (out / "contracts").mkdir(exist_ok=True)
    msgs = {"alert_m05": ALERT_M05, "graph_path_m05": GRAPH_PATH_M05}
    for dst in (out / "contracts/hero_m05_messages.json", HERE / "hero_m05_messages.json"):
        json.dump(msgs, open(dst, "w"), indent=2)
    return len(chunks), len(nodes), len(edges)


def check(out, mapped):
    errs = []
    node_ids = {n["id"] for n in read_jsonl(out / "rag/graph_nodes.jsonl")}
    for e in read_jsonl(out / "rag/graph_edges.jsonl"):
        for end in ("source", "target"):
            if e[end] not in node_ids:
                errs.append(f"dangling {end}: {e}")
    ids = {r["machine_id"] for r in read_csv(out / "master/machines.csv")}
    for i in [f"M{n:02d}" for n in range(1, 12)]:
        if i not in ids:
            errs.append(f"missing twin machine {i}")
    for old in mapped:
        txt = "".join(p.read_text() for p in (out / "rag").glob("*.jsonl"))
        if re.search(r"(?<![A-Za-z0-9_-])" + re.escape(old) + r"(?![A-Za-z0-9_])(?!-\d)", txt):
            errs.append(f"old id still present: {old}")
    for n in ("vibration_high", "bearing_wear", "m05_joint1_bearing", "replace_bearing", "bearing_6208"):
        if n not in node_ids:
            errs.append(f"hero node missing: {n}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(HERE / "out"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "raw"
        run_generator(a.seed, raw)
        mapped, emp_map = rekey(raw, out)
    counts = add_hero_and_gaps(out)
    import build_stations
    build_stations.build(out)
    errs = check(out, mapped)
    print(f"machines re-keyed: {len(mapped)}  employees re-keyed: {len(emp_map)}")
    print(f"chunks={counts[0]} nodes={counts[1]} edges={counts[2]}")
    if errs:
        print("ERRORS:"); [print(" ", e) for e in errs[:20]]; sys.exit(1)
    print("integrity: ok")


if __name__ == "__main__":
    main()
