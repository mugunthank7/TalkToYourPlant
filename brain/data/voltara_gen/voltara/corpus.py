"""Build the RAG chunk file and knowledge-graph seed (nodes/edges) from the generated datasets."""
import re
from collections import defaultdict

from .catalog import AREAS, FAMILIES, FAMILY_BY_KEY, PLANT
from .people import VENDOR_SLA

MAX_WORDS = 380


def split_markdown(text, max_words=MAX_WORDS):
    """Split a markdown document into header-led chunks that keep the doc title for context."""
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else ""
    sections, cur = [], []
    for ln in lines[1:]:
        if re.match(r"^#{2,3} ", ln) and cur:
            sections.append("\n".join(cur))
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        sections.append("\n".join(cur))
    chunks = []
    for sec in sections:
        words = sec.split()
        if len(words) <= max_words:
            chunks.append(sec)
        else:
            paras = sec.split("\n\n") if "\n\n" in sec else sec.split("\n")
            buf, n = [], 0
            for p in paras:
                w = len(p.split())
                if n + w > max_words and buf:
                    chunks.append("\n".join(buf))
                    buf, n = [], 0
                buf.append(p)
                n += w
            if buf:
                chunks.append("\n".join(buf))
    return title, [f"[{title}]\n{c.strip()}" for c in chunks if len(c.split()) > 12]


def build_rag_chunks(machines, employees, assignments, escalation, docs, wos, services, incidents, rcas, handovers,
                     vendors):
    emp = {e["employee_id"]: e for e in employees}
    mm = {m["machine_id"]: m for m in machines}
    chunks = []

    def add(source_type, source_id, text, machine_id=None, area=None, title=None, **meta):
        chunks.append(dict(chunk_id=f"c{len(chunks) + 1:07d}", source_type=source_type, source_id=source_id,
                           machine_id=machine_id, area=area or (mm[machine_id]["area"] if machine_id else None),
                           title=title or source_id, text=text, metadata=meta))

    # documents (SOPs and manuals)
    for d in docs:
        title, parts = split_markdown(d["text"])
        for i, p in enumerate(parts):
            add(d["doc_type"], d["doc_id"], p, area=d["area"], title=d["title"], family=d.get("machine_family"), part=i)

    # machine profile + escalation (who to page) chunks
    esc_by_id = {e["machine_id"]: e for e in escalation}
    for m in machines:
        fam = FAMILY_BY_KEY[m["family"]]
        add("machine_profile", m["machine_id"],
            f"Machine {m['machine_id']} is {m['name']} ({m['vendor']} {m['model']}) in {m['area_name']} ({m['bay']}), line {m['line']}. "
            f"Criticality {m['criticality']}. Installed {m['install_date']}, about {m['runtime_hours']:,} operating hours as of 2026-10-10. "
            f"Serial {m['serial']}. {m['description']} Main trade needed for repairs: {m['dominant_trade']}. "
            f"Location in plant model: x={m['x_m']} m, y={m['y_m']} m.",
            machine_id=m["machine_id"], title=f"Profile {m['machine_id']}")
        e = esc_by_id[m["machine_id"]]
        for sh in "ABC":
            c = e["on_shift_chain"][sh]

            def nm(eid):
                if not eid:
                    return "n/a"
                p = emp[eid]
                contact = p["mobile"] or p["extension"]
                return f"{p['name']} ({p['role']}, {contact})"
            hrs = {"A": "06:00-14:00", "B": "14:00-22:00", "C": "22:00-06:00"}[sh]
            eng = e["L4_engineers"]
            add("escalation", f"{m['machine_id']}-{sh}",
                f"Who to page for {m['machine_id']} ({m['name']}) on shift {sh} ({hrs}): Line Lead {nm(c['L0_line_lead'])}; "
                f"primary technician (L1) {nm(c['L1_primary_tech'])}; backup technician (L2) {nm(c['L2_backup_tech'])}; "
                f"maintenance supervisor (L3) {nm(c['L3_maintenance_supervisor'])}; area engineers (L4): reliability {nm(eng['reliability'])}, "
                f"controls {nm(eng['controls'])}, process {nm(eng['process'])}; area manager {nm(eng['area_manager'])}. "
                f"Vendor (L5): {e['L5_vendor']['vendor']} hotline {e['L5_vendor']['hotline']} ({e['L5_vendor']['contract']}, phone response {e['L5_vendor']['phone_response_h']} h, on-site {e['L5_vendor']['onsite_h']} h). "
                f"Escalation timers for criticality {m['criticality']} machines (minutes of downtime): {e['escalation_minutes']}.",
                machine_id=m["machine_id"], title=f"Escalation {m['machine_id']} shift {sh}", shift=sh)

    # employees (a few lines each, grouped)
    for e in employees:
        if e["role_code"] in ("OPR",):
            continue
        add("employee", e["employee_id"],
            f"{e['name']} ({e['employee_id']}) - {e['role']}, area {e['area'] or 'plant-wide'}, zone {e['zone'] or 'n/a'}, shift {e['shift']}. "
            f"Trade: {e['trade'] or 'n/a'} {e['skill_level'] or ''}. Certifications: {', '.join(e['certifications']) or 'none listed'}. "
            f"Contact: {e['mobile'] or e['extension']}, radio {e['radio']}, {e['email']}. Hired {e['hire_date']}.",
            area=e["area"], title=f"Employee {e['name']}", role=e["role_code"])

    # work orders (substantive ones)
    for w in wos:
        if w["wo_type"] == "CM":
            parts = ", ".join(f"{p['qty']}x {p['part_no']}" for p in w["parts_used"]) or "none"
            txt = (f"Work order {w['wo_id']} ({w['wo_type']}, {w['priority']}) on {w['machine_id']} opened {w['opened_ts']} shift {w['shift']}. "
                   f"Fault {w['fault_code']}: {w['title']}. Symptom: {w['symptom']} Diagnosis: {w['diagnosis']} Action: {w['action_taken']} "
                   f"Root cause: {w['root_cause']} ({w['root_cause_category']}). Parts: {parts}. Downtime {w['downtime_min']} min, "
                   f"escalation reached L{w['escalation_level_reached']}{', vendor involved' if w['vendor_involved'] else ''}. {w['narrative']}")
        elif w["wo_type"] == "PdM":
            txt = f"Work order {w['wo_id']} (PdM) on {w['machine_id']} opened {w['opened_ts']}. {w['symptom']} {w['diagnosis']} {w['action_taken']} {w['narrative']}"
        elif w["wo_type"] == "INSPECTION":
            txt = f"Work order {w['wo_id']} (inspection) on {w['machine_id']} at {w['started_ts']}. {w['symptom']} {w['diagnosis']} {w['action_taken']}"
        else:
            if "Findings:" not in (w["narrative"] or "") and w["status"] != "deferred" and "days after due" not in (w["narrative"] or ""):
                continue
            txt = f"Work order {w['wo_id']} (PM {w['pm_id']}) on {w['machine_id']} at {w['started_ts']}: {w['title']}. Status {w['status']}. {w['narrative']}"
        add("work_order", w["wo_id"], txt, machine_id=w["machine_id"], title=w["title"], wo_type=w["wo_type"],
            fault_code=w.get("fault_code"), date=w["opened_ts"][:10])

    for s in services:
        m0 = s["machine_ids"][0]
        parts = "; ".join(f"{p['description']} ({p['oem_part_no']}){' warranty' if p['warranty'] else ''}" for p in s["parts"]) or "none"
        add("service_log", s["service_id"],
            f"Vendor service {s['service_id']} ({s['vendor']}, {s['visit_type']}, ticket {s['ticket_no']}) on {', '.join(s['machine_ids'][:6])}"
            f"{'...' if len(s['machine_ids']) > 6 else ''}, on site {s['onsite_start']} to {s['onsite_end']}, engineer {s['engineer']}. "
            f"Findings: {s['findings']} Actions: {s['actions']} Parts: {parts}. Recommendations: {s['recommendations']} "
            f"Cost ${s['cost_usd']:,.0f}. SLA met: {s['sla_met']}. Linked work order: {s['linked_wo_id'] or 'n/a'}.",
            machine_id=m0, title=f"{s['vendor']} {s['visit_type']}", vendor=s["vendor"])

    for i in incidents:
        add("incident", i["incident_id"],
            f"Incident {i['incident_id']} ({i['type']}, severity {i['severity']}) on {i['date']} {i['time']} shift {i['shift']} in area {i['area']} "
            f"machine {i['machine_id']}: {i['description']} Immediate action: {i['immediate_action']} Root cause: {i['root_cause']}. "
            f"Corrective action: {i['corrective_actions']} Owner {i['owner']}, status {i['status']}.",
            machine_id=i["machine_id"], title=f"{i['type']} {i['incident_id']}")

    for r in rcas:
        title, parts = split_markdown(r["text"], max_words=420)
        for j, p in enumerate(parts):
            add("rca", r["rca_id"], p, machine_id=r["machine_id"], title=title, part=j)

    for h in handovers:
        if h["downtime_events"]:
            add("shift_handover", f"{h['date']}-{h['area']}-{h['shift']}", h["text"], area=h["area"],
                title=f"Handover {h['date']} {h['area']} {h['shift']}", date=h["date"])

    for v in vendors:
        add("vendor", v["vendor"],
            f"Vendor {v['vendor']}: emergency hotline {v['hotline']}, contract {v['contract']}, phone response SLA {v['response_h']} h, on-site SLA {v['onsite_h']} h, "
            f"field service contact {v['field_service_contact']}.", title=f"Vendor {v['vendor']}")
    return chunks


def build_graph(machines, employees, assignments, escalation, docs, wos, services, vendors, spare_parts):
    """Knowledge-graph seed. Nodes/edges ready for Neo4j / networkx import."""
    nodes, edges = [], []
    seen = set()

    def node(nid, label, **props):
        if nid in seen:
            return
        seen.add(nid)
        nodes.append(dict(id=nid, label=label, **props))

    def edge(a, rel, b, **props):
        edges.append(dict(source=a, rel=rel, target=b, **props))

    node("PLANT:BAP", "Plant", name=PLANT["name"])
    for code, a in AREAS.items():
        node(f"AREA:{code}", "Area", name=a["name"], bay=a["bay"])
        edge(f"AREA:{code}", "PART_OF", "PLANT:BAP")
    for v in vendors:
        node(f"VENDOR:{v['vendor']}", "Vendor", name=v["vendor"], hotline=v["hotline"], contract=v["contract"])
    for fam in FAMILIES:
        node(f"FAMILY:{fam['key']}", "MachineFamily", name=f"{fam['vendor']} {fam['model']}", criticality=fam["criticality"])
        edge(f"FAMILY:{fam['key']}", "MADE_BY", f"VENDOR:{fam['vendor']}")
        edge(f"FAMILY:{fam['key']}", "DOCUMENTED_IN", f"DOC:MAN-{fam['key']}")
        for f in fam["faults"]:
            fid = f"FAULT:{fam['key']}:{f['code']}"
            node(fid, "FaultMode", code=f["code"], description=f["desc"], severity=f["sev"], source=f["source"])
            edge(f"FAMILY:{fam['key']}", "HAS_FAULT_MODE", fid)
            edge(fid, "DOCUMENTED_IN", f"DOC:MAN-{fam['key']}")
            for pn, d, c in f["parts"]:
                node(f"PART:{pn}", "Part", description=d, unit_cost=c)
                edge(fid, "NEEDS_PART", f"PART:{pn}")
            for c in f["causes"]:
                cid = "CAUSE:" + re.sub(r"[^a-z0-9]+", "-", c.lower())[:60]
                node(cid, "Cause", text=c)
                edge(fid, "CAUSED_BY", cid)
            if f.get("sig"):
                sid = f"SENSOR:{fam['key']}:{f['sig'][0]}"
                node(sid, "SensorChannel", name=f["sig"][0])
                edge(fid, "SHOWS_IN", sid, shape=f["sig"][1])
        for s in fam["sensors"]:
            sid = f"SENSOR:{fam['key']}:{s['name']}"
            node(sid, "SensorChannel", name=s["name"], unit=s["unit"], nominal=s["nominal"], warn=s["warn"], alarm=s["alarm"])
            edge(f"FAMILY:{fam['key']}", "HAS_SENSOR", sid)
        for pm in fam["pms"]:
            pid = f"PM:{fam['key']}:{pm['id']}"
            node(pid, "PMTask", pm_id=pm["id"], task=pm["task"])
            edge(f"FAMILY:{fam['key']}", "HAS_PM", pid)
    for m in machines:
        mid = f"MACHINE:{m['machine_id']}"
        node(mid, "Machine", machine_id=m["machine_id"], name=m["name"], criticality=m["criticality"], x=m["x_m"], y=m["y_m"])
        edge(mid, "INSTANCE_OF", f"FAMILY:{m['family']}")
        edge(mid, "LOCATED_IN", f"AREA:{m['area']}")
    for e in employees:
        eid = f"EMP:{e['employee_id']}"
        node(eid, "Employee", name=e["name"], role=e["role"], shift=e["shift"], trade=e["trade"])
        if e["area"]:
            edge(eid, "WORKS_IN", f"AREA:{e['area']}")
    for a in assignments:
        edge(f"EMP:{a['employee_id']}", "ASSIGNED_TO", f"MACHINE:{a['machine_id']}", role=a["role"], shift=a["shift"])
    for esc in escalation:
        for sh, ch in esc["on_shift_chain"].items():
            order = [("L1_primary_tech", None), ("L2_backup_tech", None), ("L3_maintenance_supervisor", None)]
            prev = f"MACHINE:{esc['machine_id']}"
            for key, _ in order:
                eid = ch.get(key)
                if eid:
                    edge(prev, "ESCALATES_TO", f"EMP:{eid}", level=key, shift=sh)
                    prev = f"EMP:{eid}"
        edge(f"MACHINE:{esc['machine_id']}", "VENDOR_SUPPORT", f"VENDOR:{esc['L5_vendor']['vendor']}")
    for d in docs:
        node(f"DOC:{d['doc_id']}", "Document", title=d["title"], doc_type=d["doc_type"])
        if d["doc_type"] == "sop" and d["area"] in AREAS:
            edge(f"DOC:{d['doc_id']}", "APPLIES_TO", f"AREA:{d['area']}")
    for w in wos:
        if w["wo_type"] not in ("CM", "PdM"):
            continue
        wid = f"WO:{w['wo_id']}"
        node(wid, "WorkOrder", wo_id=w["wo_id"], wo_type=w["wo_type"], date=w["opened_ts"][:10], downtime=w["downtime_min"])
        edge(wid, "ON_MACHINE", f"MACHINE:{w['machine_id']}")
        if w["assigned_tech"]:
            edge(wid, "PERFORMED_BY", f"EMP:{w['assigned_tech']}")
        if w["fault_code"]:
            fam = next(x for x in machines if x["machine_id"] == w["machine_id"])["family"]
            edge(wid, "RESOLVED_FAULT", f"FAULT:{fam}:{w['fault_code']}")
    for s in services:
        sid = f"SVC:{s['service_id']}"
        node(sid, "ServiceVisit", visit_type=s["visit_type"], date=s["onsite_start"][:10])
        edge(sid, "BY_VENDOR", f"VENDOR:{s['vendor']}")
        for mid in s["machine_ids"]:
            edge(sid, "ON_MACHINE", f"MACHINE:{mid}")
    for p in spare_parts:
        node(f"PART:{p['part_no']}", "Part", description=p["description"], unit_cost=p["unit_cost_usd"],
             on_hand=p["on_hand"], min_stock=p["min_stock"], lead_time_days=p["lead_time_days"], bin=p["bin_location"])
    return nodes, edges
