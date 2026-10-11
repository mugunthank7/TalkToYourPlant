"""Render SOPs and per-family machine manuals as markdown documents."""
from .catalog import AREAS, FAMILIES, PLANT, TRADES
from .people import VENDOR_SLA, ESCALATION_TEMPLATE
from .sop_a import SOPS_A
from .sop_b import SOPS_B

DISCLAIMER = ("> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public "
              "OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public "
              "sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.")

REAL_FACTS = {
    "GP": [
        ("IDRA publishes the GIGAPRESS NEO 6100 at 60,000 kN clamping force, 2,400 mm die height, ~430 t weight and 20.4 x 7.4 x 6.3 m footprint.",
         "https://idragroup.com/sites/default/files/download/gigapress-catalogue-en_0.pdf"),
        ("Features: DCP hydraulic system with integrated high-flow manifold blocks, Inject Computer 3.x machine management, cell controller integration, easy-maintenance all-in-one manifolds to minimise fluid loss.",
         "https://idragroup.com/sites/default/files/download/gigapress-catalogue-en_0.pdf"),
        ("A 6,000 t Giga Press achieves fill times around 120 milliseconds; platens were redesigned and cores moved externally to improve dimensional accuracy.",
         "https://leandesign.com/?p=2932"),
        ("IDRA NEO machines use Block-Control tie-bar monitoring with automatic clamping-force adjustment, automatic toggle lubrication and a servo-driven guarding system (per NEO 1000 listing).",
         "https://www.werktuigen.com/idra-neo+1000/wt-223-58307"),
    ],
    "FANUC": [
        ("SRVO-062 BZAL: no backup battery voltage detected at the pulsecoder - mastering data lost, remastering required; SRVO-065 BLAL: low battery voltage warning, data still intact. Typical battery life 1-2 years.",
         "https://industrialmonitordirect.com/blogs/knowledgebase/fanuc-srvo-062-bzal-alarm-troubleshooting-resolution"),
        ("Typical battery: A02B-0200-K102 lithium (robot base); clear with RES_PCA then master.",
         "https://industrialmonitordirect.com/blogs/knowledgebase/fanuc-srvo-062-bzal-alarm-mastering-recovery-procedure"),
        ("SRVO-050 collision detect, SRVO-007 external emergency stop, SRVO-402 DCS alarm and SRVO-230/231 chain abnormal are among frequently encountered FANUC alarms.",
         "https://acieta.com/video-library/service"),
        ("OEM PM guidance quoted by CMMS vendors: grease replenishment for J4-J6 at about 600 hrs; full PM (gearbox oil/grease) about 3,850 hrs or 12 months.",
         "https://oxmaint.com/industries/steel-plant/industrial-robotic-arm-maintenance-steel-plants-fanuc-kuka-abb"),
    ],
    "KUKA": [
        ("KRC4 maintenance reminders: gearbox oil replacement 10,000-20,000 h or 3-4 years; inline wrist belt inspection 8,000-10,000 h; ~8 L Shell Tivela S150 per primary axis (QUANTEC).",
         "https://industrialmonitordirect.com/blogs/knowledgebase/kuka-krc4-maintenance-plans-clearing-inspection-alarms"),
        ("KR QUANTEC PA: MTBF of the whole arm improved to 400,000 hours; oil change every 20,000 operating hours.",
         "https://kuka.com/en-gb/company/press/news/2021/10/kr-quantec-pa"),
        ("KR 90/150/180 asset plans list a 20,000-hour / 5-year gear oil change; burn hazard if oil is changed right after the robot stops.",
         "https://www.getmaintainx.com/assets/kuka/industrial-robot-kr-180-r2500-extra"),
    ],
    "ABB": [
        ("OEM PM intervals quoted for ABB: about 10,000 operating hours for full PM; ISO 10218 requires periodic safety verification.",
         "https://oxmaint.com/industries/manufacturing-plant/industrial-robot-maintenance-checklist-complete"),
    ],
    "Desoutter": [
        ("Synchronous four-spindle fastening up to 20 Nm; galvanically isolated chucks protect workers near 400-800 V packs; a nominal 800 V pack contains about 198 cells in series (610-835 V).",
         "https://digitaledition.assemblymag.com/may-2023/screwdriving-battery-packs/"),
    ],
}


def _vendor_key(fam):
    return fam["vendor"]


def render_sop(s):
    refs = "\n".join(f"- {r}" for r in s["references"]) or "- Internal"
    return f"""# {s['id']}: {s['title']}

**Area:** {s['area']}  |  **Owner:** {s['owner']}  |  **Revision:** {s['revision']}  |  **Effective:** {s['effective']}

{DISCLAIMER}

{s['body']}

## References
{refs}
"""


def render_manual(fam, machines):
    ids = [m["machine_id"] for m in machines if m["family"] == fam["key"]]
    sla = VENDOR_SLA[fam["vendor"]]
    esc = ESCALATION_TEMPLATE[fam["criticality"]]
    out = []
    out.append(f"# Machine Manual: {fam['vendor']} {fam['model']} ({fam['name']})\n")
    out.append(f"**Document ID:** MAN-{fam['key']}  |  **Area:** {AREAS[fam['area']]['name']} ({fam['area']})  |  **Criticality:** {fam['criticality']}\n")
    out.append(DISCLAIMER + "\n")
    out.append("## 1. Identification\n")
    out.append(f"- **Plant machine IDs:** {', '.join(ids)}")
    out.append(f"- **Manufacturer / model:** {fam['vendor']} / {fam['model']}")
    out.append(f"- **Description:** {fam['desc']}")
    out.append(f"- **Typical cycle time:** {fam['avg_cycle_s']} s" if fam["avg_cycle_s"] else "- **Duty:** continuous")
    if fam["specs"]:
        out.append(f"- **Key specifications** ({fam['spec_source']}): " + ", ".join(f"{k} = {v}" for k, v in fam["specs"].items()))
    out.append(f"- **Typical replacement value:** about ${fam['price']:,.0f} per unit\n")

    facts = REAL_FACTS.get(fam["key"]) or REAL_FACTS.get(fam["vendor"])
    if facts:
        out.append("## 2. Verified public reference facts\n")
        for t, u in facts:
            out.append(f"- {t} (source: {u})")
        out.append("")

    out.append("## 3. Safety summary\n")
    out.append("- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.")
    if fam["area"] == "BAT":
        out.append("- Battery area: HV rules in SOP-SAF-02; thermal event response in SOP-SAF-03; use isolated tools only.")
    if fam["key"] in ("PR",):
        out.append("- Explosion-protected zone: see SOP-PNT-01 (purge fault is a Level 6 event).")
    if fam["key"] in ("GP", "DOS", "TRM"):
        out.append("- Molten metal / die water-leak hazards: see SOP-CAS-02. Hydraulic accumulators store energy: depressurize before opening circuits.")
    if "ROBO" in {f["trade"] for f in fam["faults"]}:
        out.append("- Robot cell entry only per SOP-SAF-04; T1 mode, enabling switch in hand.")
    if fam["key"] in ("LB", "BL"):
        out.append("- Class 4 laser: only laser-safety trained staff, see SOP-BAT-02.")
    out.append("")

    out.append("## 4. Operating parameters and condition-monitoring channels\n")
    out.append("| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |")
    out.append("|---|---|---|---|---|---|")
    for s in fam["sensors"]:
        out.append(f"| {s['name']} | {s['unit']} | {s['nominal']} | {s['sigma']} | {s['warn']} | {s['alarm']} |")
    out.append("\nSee SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.\n")

    out.append("## 5. Preventive maintenance schedule\n")
    for pm in fam["pms"]:
        interval = f"{pm['interval_hours']} operating hours" if pm["interval_hours"] else f"{pm['interval_days']} days"
        out.append(f"### {pm['id']}: {pm['task']}")
        out.append(f"- Interval: {interval}; typical duration {pm['duration_min']} min; trade {TRADES[pm['trade']]} ({pm['skill']})")
        if pm["steps"]:
            out.append("- Steps:")
            for i, st in enumerate(pm["steps"], 1):
                out.append(f"  {i}. {st}")
        if pm["parts"]:
            out.append("- Parts/consumables: " + "; ".join(f"{pn} ({d})" for pn, d, _ in pm["parts"]))
        out.append("")

    out.append("## 6. Fault code reference and troubleshooting\n")
    out.append("Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.\n")
    for f in fam["faults"]:
        out.append(f"### {f['code']}: {f['desc']}")
        out.append(f"- **Severity:** {f['sev']}  |  **Typical MTTR:** {f['mttr'][0]}-{f['mttr'][1]} min  |  **Trade:** {TRADES[f['trade']]}  |  **Code source:** `{f['source']}`")
        out.append("- **Probable causes:** " + "; ".join(f["causes"]))
        out.append("- **Corrective actions:**")
        for i, a in enumerate(f["actions"], 1):
            out.append(f"  {i}. {a}")
        if f["parts"]:
            out.append("- **Parts likely needed:** " + "; ".join(f"{pn} ({d})" for pn, d, _ in f["parts"]))
        if f.get("sig"):
            out.append(f"- **Early-warning signature:** channel `{f['sig'][0]}` shows {f['sig'][1].replace('_', ' ')} before failure.")
        if f["sev"] >= 3:
            out.append("- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.")
        out.append("")

    out.append("## 7. Symptom-to-cause quick guide\n")
    by_sensor = {}
    for f in fam["faults"]:
        if f.get("sig"):
            by_sensor.setdefault(f["sig"][0], []).append(f)
    if by_sensor:
        for sensor, fs in by_sensor.items():
            out.append(f"- If `{sensor}` is abnormal, think of: " + "; ".join(f"{f['code']} ({lcf(f['desc'])})" for f in fs) + ".")
    out.append("- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.")
    out.append("- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.\n")

    out.append("## 8. Spare parts list\n")
    seen = {}
    for f in fam["faults"]:
        for pn, d, c in f["parts"]:
            seen[pn] = (d, c)
    for pm in fam["pms"]:
        for pn, d, c in pm["parts"]:
            seen[pn] = (d, c)
    if seen:
        out.append("| Part no. | Description | Unit cost (USD) |")
        out.append("|---|---|---|")
        for pn, (d, c) in sorted(seen.items()):
            out.append(f"| {pn} | {d} | {c:,.0f} |")
    else:
        out.append("No machine-specific parts defined.")
    out.append("")

    out.append("## 9. Support and escalation\n")
    out.append(f"- Vendor emergency line: {sla['hotline']}  |  Contract: {sla['contract']}  |  Phone response: {sla['response_h']} h  |  On-site: {sla['onsite_h']} h")
    out.append("- Internal escalation timers (minutes of downtime): " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in esc.items()))
    out.append("- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).\n")
    out.append("## 10. Revision history\n- Rev A (2024-02-01): Initial release for start of production.\n- Rev B (2025-02-15): Added condition-monitoring thresholds.\n- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.\n")
    return "\n".join(out)


def lcf(s):
    return s[0].lower() + s[1:] if s else s


def area_protocols():
    """Per-area startup/shutdown/emergency checklists (short, templated, area-specific)."""
    docs = []
    for code, a in AREAS.items():
        text = f"""# SOP-AREA-{code}: {a['name']} Daily Start-up, Shutdown and Emergency Protocol

**Area:** {code} ({a['bay']})  |  **Revision:** B

{DISCLAIMER}

## Start-up checklist
1. Read the shift handover (SOP-MNT-03) and check open work orders for machines in {a['name']}.
2. Verify guards, light curtains and E-stops functional (test one per cell each shift).
3. Verify compressed air at 6.5-7.5 bar and cooling water supply temperature normal.
4. Machine owners complete the daily checks (see each machine manual, section 5).
5. First-off quality check before releasing production.

## Shutdown checklist
1. Complete current cycle, park robots/conveyors at home, return pallets/carriers.
2. Clean the area, remove scrap, report leaks.
3. Update the handover sheet with downtime events, watch items and locks in place.

## Emergency
- Fire, smoke, injury, HV event: pull alarm, page EHS (Level 6 per SOP-MNT-01), evacuate to the muster point for {a['bay']}.
- Machine emergency stop: identify the source, do not reset until cause is cleared; call the Line Lead.

## Contacts
Area Manager, Production Supervisor (on shift), Maintenance Supervisor of the zone and the on-call engineers are listed in the escalation dataset.
"""
        docs.append(dict(id=f"SOP-AREA-{code}", title=f"{a['name']} Daily Start-up, Shutdown and Emergency Protocol",
                         area=code, text=text))
    return docs


def all_documents(machines):
    docs = []
    for s in SOPS_A + SOPS_B:
        docs.append(dict(doc_id=s["id"], doc_type="sop", title=s["title"], area=s["area"], machine_family=None,
                         text=render_sop(s)))
    for d in area_protocols():
        docs.append(dict(doc_id=d["id"], doc_type="sop", title=d["title"], area=d["area"], machine_family=None,
                         text=d["text"]))
    for fam in FAMILIES:
        docs.append(dict(doc_id=f"MAN-{fam['key']}", doc_type="manual", title=f"{fam['vendor']} {fam['model']} manual",
                         area=fam["area"], machine_family=fam["key"], text=render_manual(fam, machines)))
    return docs
