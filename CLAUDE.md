# CLAUDE.md

Guidance for Claude Code working in this repo. Keep this file current; it is read every session.

## What this is

The **simulation engine + live 3D digital twin + dashboard** for "Talk to Your Plant", a hackathon project: an AI copilot for a (fictional) EV car assembly plant. Read `Talk_to_Your_Plant_Project_Brief.pdf` (user's Downloads) for the original pitch, and the system flowchart in `README.md` for the current scope (it superseded the brief's twin-only scope, see D-011).

Ownership (from the team whiteboard, marked M and T):
- **M (this repo, Mugu):** Data 1 (layout, employees, sensor time series, timing), simulation engine, what-if scenarios, KPI dashboard (throughput, forecast), live 3D window with moving people, fault glow/heatmap, graph-path animation, work-order beat.
- **T (teammate):** Data 2 (maintenance logs, service logs, procedures/protocols), knowledge base (graph + vector RAG), LLM brain (Gemini Flash), chat interface, diagnosing bot, voice/vision input.
- **Not M's:** anomaly detection (grey box, owner open, D-019). M exposes live state + what-if via API and renders alerts/graph paths it is sent.

Hero scenario: Weld robot 2 (`M05`) develops joint bearing wear; the twin shows the fault, the LLM explains it and can run a what-if ("keep running 2 more hours?"), then the maintenance tech walks to fix it.

The flow in one line: Data 1 -> simulation engine -> (dashboard, 3D twin, what-if) <-> LLM <- knowledge base <- Data 2; chat talks to the LLM; a work order loops back into the simulation.

## Source-of-truth docs

- `docs/STATIONS.md`: stations, machines, IDs, component node names, people roles. **Read before touching scene code.**
- `docs/ASSETS.md`: asset list, sourcing buckets, licence log, Blender workflow.
- `DECISIONS.md`: append-only decision log. **Add an entry whenever you make a non-trivial choice** (stack, format, naming, scope cut, interface change). Never rewrite old entries; supersede them.

## Build order (D-015)

1. Synthetic data (done, v1). 2. 3D live window (next; plays `schedule.json` back so people move before the engine exists). 3. SimPy engine + what-if. 4. LLM data pipeline (FastAPI tools: state, station, kpis, scenario). 5. KPI dashboard.

## Rules

1. Fictional plant, no real brands (D-002).
2. IDs and node names are a contract with the graph owner (D-008). Do not rename casually.
3. Priority is demo-first (D-007): P0 before P1 before P2. Cut unfinished work, do not half-ship it.
4. Every external model gets a row in the licence log in `docs/ASSETS.md`. Prefer CC0.
5. Blender assets are generated from scripts in `assets/source/blender/`; commit the script and the exported GLB. Do not commit `.blend1` or huge raw downloads.
6. Keep the scene under about 25 MB and 60 fps on a laptop. Instance repeated meshes and clone skinned characters with `SkeletonUtils.clone`.
7. Commits: small, imperative, one concern each. Do not commit `.env` or keys.

## Planned layout

```
twin/                 Vite + React + TS app (react-three-fiber)
  src/scene/          Plant, stations, machines, people
  src/dashboard/      KPI dashboard (throughput, forecast, scenario compare)
  src/state/          zustand stores (alerts, sensors, people scripts)
  src/data/           waypoints.json, station layout, mock sensor stream
sim/                  Simulation engine, SimPy + FastAPI (D-016)
data/plantdata/       Synthetic data generator (layout, people, tasks, sensors); outputs in data/out/
assets/
  models/             exported .glb (committed)
  textures/           PBR textures / HDRI
  source/blender/     bpy generator scripts (source of truth for hero assets)
docs/                 STATIONS.md, ASSETS.md
```

## Interface contract (draft, confirm with teammate, see D-009)

Transport: WebSocket JSON messages. The twin is a consumer; it only sends `ui_event`.

Inbound (backend -> twin):

```jsonc
// 1 Hz or faster per machine
{"type":"sensor","machine_id":"M05","ts":1760000000.0,
 "vibration_rms":0.42,"temperature_c":61.5,"motor_current_a":14.2}

{"type":"alert","machine_id":"M05","severity":"warning|critical",
 "score":0.93,
 "contributors":[{"signal":"vibration_rms","shap":0.61},{"signal":"temperature_c","shap":0.22}],
 "component_id":"m05_joint1_bearing"}

// Animate the knowledge-graph path over the 3D scene
{"type":"graph_path","nodes":[
  {"id":"vibration_high","kind":"symptom"},
  {"id":"bearing_wear","kind":"failure_mode"},
  {"id":"m05_joint1_bearing","kind":"component"},
  {"id":"replace_bearing","kind":"repair"},
  {"id":"bearing_6208","kind":"spare_part"}]}

{"type":"work_order","id":"WO-1042","machine_id":"M05","component_id":"m05_joint1_bearing",
 "spare_part":"bearing_6208","downtime_cost_per_min":20000}
```

Outbound (twin -> backend): `{"type":"ui_event","event":"inject_fault","machine_id":"M05"}` (demo trigger for judges).

What-if scenarios (LLM calls these as a tool; the simulation engine answers):

```jsonc
// LLM -> simulation engine
{"type":"run_scenario","id":"SC-7","base":"live",
 "changes":[{"op":"keep_running","machine_id":"M05","hours":2},
            {"op":"add_operator","station_id":"S06","count":1}]}
// simulation engine -> LLM and dashboard
{"type":"scenario_result","id":"SC-7",
 "kpis":{"throughput_per_hr":{"baseline":48,"scenario":31},
         "downtime_min":{"baseline":0,"scenario":74},
         "failure_probability":0.62,"cost_usd":1480000}}
```

If the simulation engine ends up in the same process as the twin (see D-013), these become function calls with the same shapes.

Twin behaviour per message: `sensor` updates HUD and gauges; `alert` turns the machine/component red with a SHAP-weighted heatmap and sets the andon light; `graph_path` highlights the 3D parts and animates a line through them; `work_order` starts the technician walk S10 -> S12 -> S06.

## Commands (fill in as the app is scaffolded)

```bash
cd data && pip install -r requirements.txt && python -m plantdata --seed 42 --out out --copy-to ../twin/public/data   # regenerate data
cd twin && npm install && npm run dev      # app
blender --background --python assets/source/blender/<asset>.py   # regenerate a model
```

## Current status

- [x] Repo skeleton, docs, decisions
- [x] System flowchart in README (whiteboard v1 -> improved v2, D-011, D-012)
- [x] Decisions D-013..D-017: SimPy engine, M owns Data 1 + anomaly detection, build order
- [x] Synthetic data generator `data/plantdata/` (layout, 24 employees, tasks, transfer times, per-person schedules, 5 scenarios with sensors + production output, 30-day history with RUL labels); spec in `docs/DATA_SPEC.md`
- [x] `twin/` v0 (Vite + R3F): floor, stations, walkways, conveyor + cars, placeholder machines, people (capsules) playing `schedule.json`, M05 fault glow, HUD (clock, speed, shift, jump to alert, camera views). Run: `cd twin && npm run dev` (port 5180) the schedule
- [ ] Install Blender, confirm headless export works
- [ ] P0 assets: weld robot (rigged), conveyor, press, BIW
- [x] HUD v1 matching the ChatGPT concept mockup (top bar, live plant state, KPIs, forecast, timeline, what-if, camera shortcuts) with live numbers from `kpi.json`
- [x] 3D realism pass v1: CC0 HDRI + concrete floor + Poly Haven props (licence log in docs/ASSETS.md), limbed workers with walk/work/crouch, fenced weld cells + andon lights, car bodies, articulated robots with sparks and the glowing `m05_joint1_bearing` ring, bloom, adaptive quality (`?q=low` forces low)
- [x] Compact 128x72 layout, material flow (AGVs, forklift, cart), car built along the belt, factory shell with walls/crane/HDRI backdrop (D-027)
- [x] Dashboard tab (in-depth KPIs): tiles, cumulative output, OEE, loss waterfall, forecast, what-if, 30-day trend, downtime Pareto, machine health, incidents. Data: `data/out/dashboard.json` + `kpi.json`
- [x] Blender 5.2.2 installed at /Applications/Blender.app (CLI: /Applications/Blender.app/Contents/MacOS/Blender)
- [x] Detailed procedural station models from ChatGPT references (docs/reference/): all 12 stations (S01 to S12) in `twin/src/scene/stations/`, built with the kit in `scene/kit.tsx`. Preview one with `?station=S11&clean=1&q=low`
- [x] S04 to S07 from references incl. S06 alert effects (halo, banner, callout, vibration trend, technician trail, technician carries the bearing box). URL helpers: `?station=S06&clean=1&t=18900&pause=1&q=low`
- [x] Fault engine (twin/src/plant.ts): faults stop the belt (cars freeze), starve downstream and block upstream stations, blink red, on-call technician walks bay -> spares -> machine; fault simulator in the HUD; people have spots inside rooms and sit at breaks; belt keep-out for people
- [x] HUD v2: forecast-aware live plant state (yellow = risk/starved/blocked), compact event timeline, 16 camera shots + tour/orbit/follow car/follow tech, 'Simulate a fault'
- [x] Dashboard help popovers (?) and hover readouts on every chart; throughput forecast shows 'if repaired' vs 'if ignored'
- [ ] (old) NEXT: people spots inside the new rooms (supervisor at the S11 desk, seated breaks, technician at the S10 bench, S12 pickup, sit pose), check performance on a real GPU, replace Cells/old safety zone code, then SimPy engine detailed models in this order: S11, S12, S10, S09, S02, S03 (then S01, S08); Blender-built hero models (press, robot, conveyor) and rigged Mixamo/Quaternius characters replacing the procedural ones; match the ChatGPT mockup's density (racks, glass control room, more props) (Blender weld robot etc.) and Mixamo characters replacing the placeholders
- [ ] Replay `scenarios/hero_timely_repair_sensors.parquet` as the mock stream + fault glow on M05
- [ ] SimPy engine + what-if + FastAPI tool endpoints (D-016)
- [ ] KPI dashboard
- [ ] Wire to real WebSocket
