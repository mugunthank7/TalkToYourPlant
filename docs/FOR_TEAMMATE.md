# For the knowledge / LLM side: what you need from the twin

Repo: https://github.com/mugunthank7/TalkToYourPlant . Twin and simulation are mine (blue boxes in the README flowchart). Yours is the green side. Please tell me if any ID or message below does not fit your graph.

## 1. Shared IDs (use these exactly)
Full list with coordinates: `docs/STATIONS.md` and `data/out/layout.json`.

| Station | Name | Machine(s) |
|---------|------|------------|
| S01 | Coil yard | M10 Decoiler |
| S02 | Casting and press | M01 Casting press, M02 Press transfer robot |
| S03 | Parts buffer | M11 Rack AGV |
| S04 | Framing | M03 Framing fixture, M06 Main conveyor |
| S05 | Weld cell A | M04 Weld robot 1 |
| S06 | Weld cell B | **M05 Weld robot 2 (hero)** |
| S07 | Inspection gate | M07 Vision gate |
| S08 | Battery module line | M08 Module stacker |
| S09 | Pack closing and EOL test | M09 Pack sealer |
| S10 | Maintenance bay | none |
| S11 | Control room and break room | none |
| S12 | Spare parts cage | none |

Component IDs are `<machine id lower>_<component>`, for example `m05_joint1_bearing`, `m05_servo_motor`, `m05_gearbox`, `m05_weld_gun`, `m05_cable_harness`, `m05_controller_cabinet`. Hero fault: **M05, `m05_joint1_bearing`**, spare part `bearing_6208`.

## 2. What you can reuse
Run once: `cd data && pip install -r requirements.txt && python -m plantdata --seed 42 --out out`
- `data/out/history/failure_modes.csv`: 35 failure modes (machine type, component, symptom, cause, repair, spare part, supplier, repair time, part cost). Ready seed for Machine, Component, Failure Mode, Cause, Repair, Spare Part, Supplier. Estimates, edit freely.
- `data/out/history/maintenance_work_orders.csv` and `downtime_events.csv`: a year of estimated work orders and downtime. Use as log text or as graph evidence.
- `data/out/employees.csv`, `tasks.csv`: people and tasks, if you need them.
- Sensors for anomaly detection (nobody owns this yet): `data/out/scenarios/healthy_realistic_sensors.parquet` to train, `hero_timely_repair_sensors.parquet` to test. Ground truth columns: `fault_label`, `degradation`, `rul_s`.

## 3. Messages (WebSocket JSON)
Twin consumes; details and field names in `CLAUDE.md`, section "Interface contract".
- `sensor`: machine_id, ts, vibration_rms, temperature_c, motor_current_a (from the simulation, I send this to you and to the twin).
- `alert`: machine_id, severity, score, contributors[{signal, shap}], component_id (you or whoever owns anomaly detection send this).
- `graph_path`: ordered nodes `{id, kind}` with kinds symptom, failure_mode, component, repair, spare_part. The twin animates it across the 3D scene. Node IDs for components must be the component IDs above.
- `work_order`: id, machine_id, component_id, spare_part, downtime_cost_per_min. The technician in the twin walks to the machine.
- `run_scenario` (you to me) and `scenario_result` (me to you): what-if requests and KPI answers.

## 4. The engine is live (SimPy plus FastAPI, see `sim/README.md`)
Run `cd sim && .venv/bin/uvicorn plantsim.api:app --port 8000`. `GET /tools` returns function-calling schemas for your LLM: `get_plant_state`, `get_station`, `get_machine_health`, `get_kpis`, `get_diagnosis_context` (sensor evidence, failure-mode candidates, act-now vs wait cost), `run_what_if`, `create_work_order`, `inject_fault`. Execute with `POST /tools/{name}`. A WebSocket at `/ws` streams state and events (alert, fault, work_order, dispatched, repair_*).

## 5. Facts to quote
- Downtime cost: $38,000 per minute, large automotive plant (Siemens, True Cost of Downtime 2024). See `docs/SOURCES.md`.
- At the alert on M05 there are about 53 minutes of remaining useful life before it would fail.
- Everything here is synthetic.

## 6. Questions for you
1. ~~Who builds anomaly detection?~~ Done by M inside the engine (docs/ANOMALY.md). Use `GET /anomaly/{machine}` or the `get_anomaly_report` tool; alerts carry `contributors` and an RUL interval.
2. Are `failure_modes.csv` and the component names OK for your graph, or do you want different IDs?
3. Which transport: WebSocket from your FastAPI app, or should I host the one FastAPI app?
