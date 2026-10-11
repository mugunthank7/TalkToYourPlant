#!/usr/bin/env python3
"""Voltara Motors synthetic EV-plant data generator.

Usage:  python3 generate.py --out output --seed 42
Produces master data, logs, SOPs/manuals, RAG chunks and a knowledge-graph seed.
Everything is deterministic for a given seed.
"""
import argparse
import csv
import json
import os
import random
import sys
import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voltara import catalog, people, workorders, documents, corpus  # noqa: E402


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")


def write_csv(path, rows, fields=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        return
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, default=str) if isinstance(v, (list, dict)) else v) for k, v in r.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="output")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    out = args.out

    print("master data...")
    machines = people.build_machines(rng)
    employees = people.build_employees(rng, machines)
    roster = people.build_roster(rng, employees)
    assignments = people.build_assignments(rng, machines, employees)
    vendors = people.build_vendors(rng)
    escalation = people.build_escalation(machines, employees, assignments)
    oncall = people.build_oncall(rng, employees)

    print("logs...")
    wos, daily = workorders.generate_work_orders(rng, machines, employees, assignments)
    services = workorders.generate_service_logs(rng, machines, wos, employees)
    incidents, rcas = workorders.generate_incidents(rng, machines, wos, employees)
    handovers = workorders.generate_handover_notes(rng, machines, wos, employees)
    parts = workorders.generate_spare_parts(rng, wos)

    print("documents...")
    docs = documents.all_documents(machines)

    print("rag + graph...")
    chunks = corpus.build_rag_chunks(machines, employees, assignments, escalation, docs, wos, services, incidents,
                                     rcas, handovers, vendors)
    nodes, edges = corpus.build_graph(machines, employees, assignments, escalation, docs, wos, services, vendors, parts)

    print("writing files...")
    # master
    write_json(f"{out}/master/plant.json", dict(plant=catalog.PLANT, areas=catalog.AREAS, trades=catalog.TRADES,
                                                 roles=people.ROLES, certifications=people.CERTS, zones=people.ZONES,
                                                 as_of=str(people.AS_OF), start_of_production=str(people.SOP_DATE)))
    write_json(f"{out}/master/machines.json", machines)
    write_csv(f"{out}/master/machines.csv", machines)
    write_json(f"{out}/master/layout.json", [dict(machine_id=m["machine_id"], area=m["area"], line=m["line"], x_m=m["x_m"], y_m=m["y_m"],
                                                  z_m=m["z_m"], rotation_deg=m["rotation_deg"], family=m["family"]) for m in machines])
    write_json(f"{out}/master/machine_catalog.json", [{k: v for k, v in f.items()} for f in catalog.FAMILIES])
    write_json(f"{out}/master/employees.json", employees)
    write_csv(f"{out}/master/employees.csv", employees)
    write_csv(f"{out}/master/roster.csv", roster)
    write_csv(f"{out}/master/machine_assignments.csv", assignments)
    write_json(f"{out}/master/escalation_matrix.json", escalation)
    write_csv(f"{out}/master/oncall_rota.csv", oncall)
    write_csv(f"{out}/master/vendors.csv", vendors)
    write_csv(f"{out}/master/spare_parts.csv", parts)
    # logs
    write_jsonl(f"{out}/logs/work_orders.jsonl", wos)
    flat = []
    for w in wos:
        r = dict(w)
        r["parts_used"] = json.dumps(w["parts_used"])
        r["sensor_snapshot"] = json.dumps(w["sensor_snapshot"]) if w["sensor_snapshot"] else ""
        flat.append(r)
    write_csv(f"{out}/logs/work_orders.csv", flat)
    write_csv(f"{out}/logs/daily_checks.csv", daily)
    write_jsonl(f"{out}/logs/service_logs.jsonl", services)
    write_csv(f"{out}/logs/incidents.csv", incidents)
    write_jsonl(f"{out}/logs/shift_handover_notes.jsonl", handovers)
    for r in rcas:
        os.makedirs(f"{out}/logs/rca_reports", exist_ok=True)
        with open(f"{out}/logs/rca_reports/{r['rca_id']}_{r['machine_id']}.md", "w") as f:
            f.write(r["text"])
    # docs
    for d in docs:
        sub = "sops" if d["doc_type"] == "sop" else "manuals"
        os.makedirs(f"{out}/docs/{sub}", exist_ok=True)
        with open(f"{out}/docs/{sub}/{d['doc_id']}.md", "w") as f:
            f.write(d["text"])
    # rag / graph
    write_jsonl(f"{out}/rag/rag_chunks.jsonl", chunks)
    write_jsonl(f"{out}/rag/graph_nodes.jsonl", nodes)
    write_jsonl(f"{out}/rag/graph_edges.jsonl", edges)
    # simulator contract (shared with the twin side)
    write_json(f"{out}/contracts/simulator_interface.json", dict(
        description="Sensor channels, thresholds and fault signatures per machine family; use to drive the simulator and anomaly detection.",
        families={f["key"]: dict(vendor=f["vendor"], model=f["model"], area=f["area"], criticality=f["criticality"],
                                 sensors=f["sensors"],
                                 fault_signatures=[dict(code=x["code"], sev=x["sev"], sensor=x["sig"][0], shape=x["sig"][1],
                                                        mttr_min=x["mttr"][0], mttr_max=x["mttr"][1], weight=x["w"]) for x in f["faults"] if x.get("sig")])
                  for f in catalog.FAMILIES},
        bad_actors={k: dict(fault_code=v[0], window_start=str(v[2]), window_end=str(v[3])) for k, v in workorders.BAD_ACTORS.items()}))

    words = sum(len(c["text"].split()) for c in chunks)
    stats = dict(machines=len(machines), employees=len(employees), roster_rows=len(roster), assignments=len(assignments),
                 work_orders=len(wos), daily_checks=len(daily), service_logs=len(services), incidents=len(incidents),
                 rca_reports=len(rcas), handover_notes=len(handovers), documents=len(docs), rag_chunks=len(chunks),
                 rag_words=words, graph_nodes=len(nodes), graph_edges=len(edges))
    write_json(f"{out}/stats.json", stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
