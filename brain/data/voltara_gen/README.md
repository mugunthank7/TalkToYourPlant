# Voltara Motors - Bastrop Assembly Plant: synthetic EV plant dataset

Fictional EV plant (Voltara V1 sedan / V2 crossover, ~38 vehicles/hour) built for the "talk to your plant" digital-twin demo.
Everything is **synthetic and deterministic** (`python3 generate.py --out output --seed 42`, ~3 s, standard library only).
Reference date ("now") = **2026-10-10**; history covers 2024-10-01 to 2026-10-10.

## What you get (default seed)
| Item | Count |
|---|---|
| Machines (39 families, 10 areas) | 119 |
| Employees (all roles, 3 shifts) | 452 |
| Roster rows (90 days back + 14 ahead) | 47,008 |
| Work orders (PM / corrective / condition alerts / inspections) | ~20,100 |
| Daily check records | ~17,800 |
| Vendor service logs | ~780 |
| Incidents + RCA reports | 340 + 60 |
| Shift handover notes (last 120 days) | 2,580 |
| SOPs/protocols + machine manuals | 83 documents |
| RAG chunks (ready to embed) | ~11,100 (~655k words) |
| Knowledge-graph seed | ~5.7k nodes, ~18k edges |

## Layout
```
master/   plant.json  machines.csv|json  machine_catalog.json (faults, PM tasks, sensors per family)
          employees.csv|json  roster.csv  machine_assignments.csv  escalation_matrix.json
          oncall_rota.csv  vendors.csv  spare_parts.csv  layout.json (x,y for the 3-D plant)
logs/     work_orders.jsonl|csv  daily_checks.csv  service_logs.jsonl  incidents.csv
          shift_handover_notes.jsonl  rca_reports/*.md
docs/     sops/*.md (44)  manuals/*.md (39, one per machine family)
rag/      rag_chunks.jsonl  graph_nodes.jsonl  graph_edges.jsonl
contracts/simulator_interface.json   sensor channels, thresholds, fault signatures, "bad actor" storylines
```

## Answering "who do I page?"
`master/escalation_matrix.json` has, per machine and shift: Line Lead -> L1 primary tech -> L2 backup tech -> L3 maintenance supervisor,
plus L4 area engineers (reliability/controls/process), L5 vendor hotline + SLA, L6 plant management, and the downtime-minute timers by criticality (A/B/C).
`rag_chunks.jsonl` contains one natural-language "Who to page" chunk per machine per shift (357) built from it. SOP-MNT-01 documents the protocol.
Mobile numbers use the fictional 555-01xx range; other staff have extensions and radio call signs.

## Linking the twin side (M) and the brain side (T)
- Every corrective work order has `sensor_snapshot` = channel readings at fault time (ground truth for anomaly detection / SHAP).
- `contracts/simulator_interface.json` lists, per family, channels with nominal/sigma/warn/alarm and each fault's signature (`sensor`, `shape`: drift_up / drift_down / decay / spike).
- **Live storylines** (still unfolding in the last 3 weeks, good for the demo): CAS-GP-01 shot-slow / accumulator pre-charge, PNT-PR-04 bell speed,
  BAT-BL-01 laser power (protective glass), BIW-WK-03 gearbox oil leak, UTL-CP-02 compressor discharge temperature (summer), GA-TQ-07 torque NOKs.
- `SOP-OPS-02` encodes the rules for questions like *"can we keep running 2 more hours?"*.
- Graph schema: `Machine -INSTANCE_OF-> MachineFamily -HAS_FAULT_MODE-> FaultMode -NEEDS_PART-> Part`, `FaultMode -CAUSED_BY-> Cause`,
  `FaultMode -SHOWS_IN-> SensorChannel`, `Employee -ASSIGNED_TO-> Machine`, `Machine -ESCALATES_TO-> Employee`, `WorkOrder -ON_MACHINE/PERFORMED_BY/RESOLVED_FAULT-`, `*-DOCUMENTED_IN-> Document`.

## How real is it?
- Machine makes/models are real products (IDRA, KUKA, FANUC, ABB, Duerr, TRUMPF, Desoutter, Atlas Copco ...). Facts verified against public sources are tagged
  `oem_public` (e.g. FANUC SRVO-062/065/050/007/402 meanings and battery guidance, KUKA oil-change intervals, IDRA Giga Press specs, Desoutter 4-spindle 20 Nm fastening).
  See `SOURCES.md`. All other fault codes, part numbers, intervals and numbers are `synthetic`.
- The manuals are **synthetic composites, not copies of OEM manuals** (OEM manuals are copyright-protected and mostly behind customer logins, so they were not scraped).
  To add real manuals you are licensed to use, drop PDFs into `real_manuals/` and run `python3 ingest_real_manuals.py`.
- Names, phone numbers, emails (`@voltara-motors.example`) are fictional.

## Checks
`python3 validate.py output` verifies referential integrity (machines, employees, escalation chain, graph edges), fault-code/family consistency,
commissioning dates, phone-number ranges and duplicates. Last run: 0 errors, 0 warnings.
