#!/usr/bin/env python3
"""Integrity checks on generated output. Usage: python3 validate.py output"""
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

out = sys.argv[1] if len(sys.argv) > 1 else "output"
errs, warns = [], []


def jl(p):
    with open(os.path.join(out, p)) as f:
        return [json.loads(x) for x in f]


def cs(p):
    with open(os.path.join(out, p)) as f:
        return list(csv.DictReader(f))


machines = json.load(open(f"{out}/master/machines.json"))
emps = json.load(open(f"{out}/master/employees.json"))
esc = json.load(open(f"{out}/master/escalation_matrix.json"))
wos = jl("logs/work_orders.jsonl")
svc = jl("logs/service_logs.jsonl")
chunks = jl("rag/rag_chunks.jsonl")
nodes = jl("rag/graph_nodes.jsonl")
edges = jl("rag/graph_edges.jsonl")
assign = cs("master/machine_assignments.csv")
daily = cs("logs/daily_checks.csv")
inc = cs("logs/incidents.csv")

mids = {m["machine_id"] for m in machines}
eids = {e["employee_id"] for e in emps}

if len(mids) != len(machines): errs.append("duplicate machine ids")
if len(eids) != len(emps): errs.append("duplicate employee ids")
if len({w["wo_id"] for w in wos}) != len(wos): errs.append("duplicate WO ids")
if len({c["chunk_id"] for c in chunks}) != len(chunks): errs.append("duplicate chunk ids")

phones = [e["mobile"] for e in emps if e["mobile"]]
if len(phones) != len(set(phones)): errs.append("duplicate mobile numbers")
for p in phones:
    if not re.fullmatch(r"\d{3}-555-01\d\d", p): errs.append(f"phone outside fictional range: {p}")

for w in wos:
    if w["machine_id"] not in mids: errs.append(f"{w['wo_id']} unknown machine")
    if w["assigned_tech"] and w["assigned_tech"] not in eids: errs.append(f"{w['wo_id']} unknown tech {w['assigned_tech']}")
    if w["closed_ts"] < w["opened_ts"]: errs.append(f"{w['wo_id']} closed before opened")
    if w["opened_ts"][:10] > "2026-10-10" or w["closed_ts"][:10] > "2026-10-12": errs.append(f"{w['wo_id']} in the future")
    if w["wo_type"] == "CM" and not (w["fault_code"] and w["diagnosis"] and w["action_taken"]): errs.append(f"{w['wo_id']} CM incomplete")
    if w["wo_type"] == "CM" and w["downtime_min"] <= 0: errs.append(f"{w['wo_id']} zero downtime")
mach_family = {m["machine_id"]: m["family"] for m in machines}
cat = json.load(open(f"{out}/master/machine_catalog.json"))
codes = {f["key"]: {x["code"] for x in f["faults"]} for f in cat}
for w in wos:
    if w["wo_type"] == "CM" and w["fault_code"] not in codes[mach_family[w["machine_id"]]]:
        errs.append(f"{w['wo_id']} fault code not valid for family")

comm = {m["machine_id"]: m["commissioned_date"] for m in machines}
for w in wos:
    if w["opened_ts"][:10] < comm[w["machine_id"]] and w["wo_type"] in ("CM", "PdM", "PM"):
        errs.append(f"{w['wo_id']} opened before machine commissioned")
for s_ in svc:
    for m_ in s_["machine_ids"]:
        if s_["onsite_start"][:10] < comm[m_]:
            errs.append(f"{s_['service_id']} before commissioning of {m_}")
for a in assign:
    if a["machine_id"] not in mids or a["employee_id"] not in eids: errs.append(f"bad assignment {a}")
for e in esc:
    for sh, ch in e["on_shift_chain"].items():
        for k, v in ch.items():
            if k.startswith("L") and k != "L0_operator_action" and v and v not in eids:
                errs.append(f"escalation unknown employee {v}")
        if not ch["L1_primary_tech"]: warns.append(f"{e['machine_id']} shift {sh}: no primary tech")
        if not ch["L3_maintenance_supervisor"]: warns.append(f"{e['machine_id']} shift {sh}: no supervisor")
for s in svc:
    for m in s["machine_ids"]:
        if m not in mids: errs.append(f"{s['service_id']} unknown machine")

node_ids = {n["id"] for n in nodes}
dangling = [e for e in edges if e["source"] not in node_ids or e["target"] not in node_ids]
if dangling:
    errs.append(f"{len(dangling)} dangling graph edges, e.g. {dangling[0]}")

for c in chunks:
    if len(c["text"].split()) < 8: warns.append(f"tiny chunk {c['chunk_id']}")

# an operator may not be on two machines of different areas, and every machine must have a primary tech on each shift
print("machines:", len(machines), "employees:", len(emps), "work orders:", len(wos), Counter(w['wo_type'] for w in wos))
print("shifts covered with primary tech:", sum(1 for e in esc for sh in 'ABC' if e['on_shift_chain'][sh]['L1_primary_tech']), "of", len(esc) * 3)
print("RAG chunks:", len(chunks), "by type:", dict(Counter(c['source_type'] for c in chunks)))
print("RAG words:", sum(len(c['text'].split()) for c in chunks))
print("errors:", len(errs), "warnings:", len(warns))
for e in errs[:25]: print("ERR", e)
for w in warns[:10]: print("WARN", w)
sys.exit(1 if errs else 0)
