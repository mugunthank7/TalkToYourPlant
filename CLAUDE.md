# CLAUDE.md

Guidance for Claude Code working in this repo. Keep this file current; it is read every session.

## What this is

The **live 3D digital twin** for "Talk to Your Plant", a hackathon project: an AI copilot for a (fictional) EV car assembly plant. Read `Talk_to_Your_Plant_Project_Brief.pdf` (user's Downloads) for the full pitch. A teammate owns RAG, GraphRAG, multimodal (voice/vision) and anomaly detection. **This repo owns only the twin**: realistic 3D plant, moving people, sensor visualisation, fault glow/heatmap, graph-path animation, work-order beat.

Hero scenario: Weld robot 2 (`M05`) develops joint bearing wear; the twin shows the fault, then the maintenance tech walks to fix it.

## Source-of-truth docs

- `docs/STATIONS.md`: stations, machines, IDs, component node names, people roles. **Read before touching scene code.**
- `docs/ASSETS.md`: asset list, sourcing buckets, licence log, Blender workflow.
- `DECISIONS.md`: append-only decision log. **Add an entry whenever you make a non-trivial choice** (stack, format, naming, scope cut, interface change). Never rewrite old entries; supersede them.

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
  src/state/          zustand stores (alerts, sensors, people scripts)
  src/data/           waypoints.json, station layout, mock sensor stream
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

Twin behaviour per message: `sensor` updates HUD and gauges; `alert` turns the machine/component red with a SHAP-weighted heatmap and sets the andon light; `graph_path` highlights the 3D parts and animates a line through them; `work_order` starts the technician walk S10 -> S12 -> S06.

## Commands (fill in as the app is scaffolded)

```bash
cd twin && npm install && npm run dev      # app
blender --background --python assets/source/blender/<asset>.py   # regenerate a model
```

## Current status

- [x] Repo skeleton, docs, decisions
- [ ] Install Blender, confirm headless export works
- [ ] Scaffold `twin/` (Vite + R3F), empty plant with floor and lighting
- [ ] P0 assets: weld robot (rigged), conveyor, press, BIW
- [ ] P0 people: operator + maintenance tech with walk/idle/work
- [ ] Mock sensor stream + fault glow on M05
- [ ] Technician scripted walk on work order
- [ ] Wire to real WebSocket
