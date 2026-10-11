# Decisions

Append-only log. New decision = new entry at the bottom with the next ID. To change one, add a new entry that supersedes it; do not edit history.

Format: **D-NNN, title** | date | status (`accepted`, `superseded by D-NNN`, `open`) | context, decision, consequences.

---

## D-001, This repo owns the digital twin only | 2026-10-10 | accepted
**Context:** Two people. The friend builds RAG, multimodal (voice/vision), knowledge graph, anomaly detection. This repo is the live 3D digital twin.
**Decision:** Keep the twin in its own repo (`talk-to-your-plant-twin`) with a narrow interface contract (CLAUDE.md, "Interface contract"). The twin consumes events and renders; it does not run models.
**Consequences:** We can work in parallel without merge conflicts. If the team prefers a monorepo later, move `twin/` into it unchanged (new decision).

## D-002, Fictional plant, no real brands | 2026-10-10 | accepted
**Context:** The brief says the plant is fictional to avoid trademark and credibility issues.
**Decision:** The plant is "Voltline EV Works". No real automaker, robot vendor, logos or liveries in models, textures or UI.
**Consequences:** Downloaded models with real branding are rejected or re-skinned.

## D-003, Stack: React + Three.js via react-three-fiber, Vite, TypeScript | 2026-10-10 | accepted
**Context:** The brief specifies React + Three.js. Needs fast iteration and good GLB/animation tooling.
**Decision:** Vite + React + TypeScript, `@react-three/fiber`, `@react-three/drei` (`useGLTF`, `useAnimations`, helpers), zustand for twin state.
**Consequences:** Declarative scene, easy GLB loading and animation mixing. Team must be comfortable with R3F.

## D-004, Asset sourcing is hybrid | 2026-10-10 | accepted
**Context:** User wants real 3D models and moving people. Options: model everything in Blender with Claude, or download from the web.
**Decision:** Three buckets (full detail in docs/ASSETS.md): (A) Blender + Claude `bpy` scripts for hero machines that need named, glowable, animatable parts; (B) free CC0/CC-BY web models for generic props; (C) Mixamo/Quaternius rigged characters for people.
**Consequences:** Hero assets are reproducible from scripts and have clean node names. Web assets save time but need a licence log. Blender must be installed.

## D-005, Model format: GLB, 1 unit = 1 m, Y-up, compressed | 2026-10-10 | accepted
**Decision:** All models ship as `.glb`, meshopt or Draco compressed, scene total under about 25 MB. Hero machine parts use snake_case node names that equal the knowledge-graph `Component.id`.
**Consequences:** One naming contract links the 3D scene, the sensor stream and the graph. Enables part-level glow and graph-path highlighting.

## D-006, People: animated, waypoint-driven, role scripts | 2026-10-10 | accepted
**Context:** Need people moving to sell realism, but pathfinding and crowds can eat the build.
**Decision:** 6 to 7 characters in four roles. Movement along a hand-authored waypoint graph (no crowd simulation), animation state machine per role (idle/walk/work). The maintenance technician has a scripted sequence triggered by the work-order event. Robots visually pause when a person is in their safety zone.
**Consequences:** Cheap, predictable, demo-safe. No emergent behaviour, which is fine for a 90-second demo.

## D-007, Hero scenario is the single source of the P0 scope | 2026-10-10 | accepted
**Decision:** P0 stations/assets are exactly those needed for the hero scenario: press, conveyor, framing, two weld cells (M05 is the hero), maintenance bay, spare cage, andon, plus people. Everything else is P1/P2 and is cut at hour 16 of the build plan if unfinished.
**Consequences:** Protects the demo. P2 items may be cheap placeholders (a labelled box).

## D-008, Source IDs are shared with the graph owner | 2026-10-10 | accepted
**Decision:** Station IDs (`S01..S12`), machine IDs (`M01..M11`) and component node names in docs/STATIONS.md are the shared contract. Changes require a new decision entry and a message to the data owner.

## D-009, Sensor data is simulated in the twin until the backend is ready | 2026-10-10 | open
**Context:** The brief has FastAPI + WebSockets streaming simulated sensors; the friend owns backend/data.
**Decision (provisional):** The twin ships with a local mock stream that matches the contract so we are never blocked, then switches to the real WebSocket by an env flag.
**To confirm with friend:** exact message schema (draft in CLAUDE.md).

## D-010, Repo hosting | 2026-10-10 | open
**Context:** `gh` is not logged in on this machine yet.
**Decision needed:** repo name and visibility (private while building, public for LinkedIn/resume at submission). Proposed: `talk-to-your-plant-twin`, private first.

## D-011, Scope grows from "twin" to "simulation engine + twin + dashboard" | 2026-10-10 | accepted
**Context:** The team whiteboard shows a simulation engine as the center, fed by Data 1 (layout, employees, sensor time series, timing) and producing what-if scenarios, a KPI dashboard (KPIs, throughput, forecast) and the live 3D window. The original brief only had a fault demo. Whiteboard owner marks: M = this repo, T = teammate (knowledge base, LLM, chat).
**Decision:** This repo owns Data 1, the simulation engine, what-if scenarios, the dashboard and the 3D twin. Teammate owns Data 2, the knowledge base, LLM and chat. Supersedes the narrow scope in D-001; the interface contract in CLAUDE.md remains.
**Consequences:** More work for M. Simulation engine becomes P0 because the twin, dashboard and scenarios all read from it. Dashboard and what-if are P1 behind the hero fault scenario (D-007 still applies).

## D-012, Flow v2 improvements over the whiteboard | 2026-10-10 | accepted
**Decision:** The README flowchart keeps the whiteboard structure and adds: (1) anomaly detection with SHAP between the sensor stream and the LLM, so alerts are explainable; (2) the LLM drives what-ifs through a `run_scenario` tool and gets `scenario_result` back; (3) a closed loop: work order -> simulation -> technician agent walks to the machine -> fault clears; (4) a synthetic data generator feeding both Data 1 and Data 2; (5) chat accepts voice and photo as well as text.
**Consequences:** One simulated state drives dashboard, 3D and LLM, so numbers always agree across all three views.

## D-013, Where the simulation engine lives | 2026-10-10 | accepted (SimPy, Python; see D-016)
**Options:** (a) Python + SimPy as a FastAPI service next to anomaly detection and the LLM backend, twin renders streamed state; (b) TypeScript in the browser (Web Worker), no backend needed for the visuals.
**Leaning:** (a) for batch what-if runs (compare baseline vs scenario) and one language with the ML code; keep a thin TS fallback that replays recorded state if the backend is down during the demo.
**Needs:** agreement with the teammate and the decision on who hosts the FastAPI app.

## D-014, Ownership of anomaly detection and synthetic data | 2026-10-10 | accepted (M owns Data 1 and anomaly detection; see D-015)
**Context:** The whiteboard does not show anomaly detection; the brief has it (Isolation Forest + SHAP). Both sides need synthetic data.
**Proposal:** M generates Data 1 (sensor streams with injected bearing-wear signatures, shifts, timings) and runs anomaly detection on the simulated stream; T generates Data 2 (manuals, logs, graph). Confirm with teammate.

## D-015, Build order and M's deliverables | 2026-10-10 | accepted
**Context:** M's own list: (1) synthetic data for layout, employees, sensor time series, per-person task timings, task assignment, and item transfer times between stations; (2) simulation engine plus what-if; (3) data pipeline so the LLM can pull state from the simulation and diagnose; (4) KPI/throughput-forecast dashboard; (5) a good-looking 3D live window with everyone moving. Stated priority: synthetic data first, 3D second.
**Decision:** Order is (1) synthetic data, (2) 3D live window, (3) simulation engine, (4) LLM data pipeline, (5) dashboard. The generator also emits a scripted per-person schedule so the 3D window can play back full motion before the simulation engine exists. The engine then replaces the playback with the same message shape.
**Consequences:** 3D is never blocked on the engine. The schedule JSON is the temporary stand-in for engine output.

## D-016, Simulation engine: SimPy (Python) behind FastAPI | 2026-10-10 | accepted (revisit if SimPy blocks us)
**Context:** Needs what-if runs faster than real time, sensor/anomaly code in Python anyway, and a clean way for the LLM to query state.
**Options:** SimPy (process-based discrete-event, pure Python, tiny API, great for stations/queues/operators as resources); Salabim (adds built-in animation we do not need); Ciw (queueing networks only, too limited); custom TypeScript engine in the browser (no backend needed but no shared code with ML/LLM side); AnyLogic (proprietary).
**Decision:** SimPy. Machines are processes, operators are `Resource`s, vehicles are items flowing through stations with the generated cycle and transfer times. Real-time mode streams state over a WebSocket; what-if runs clone the config and run to completion headless. FastAPI exposes `GET /state`, `GET /station/{id}`, `GET /kpis`, `POST /scenario` which are also the LLM tools.
**Consequences:** One Python codebase for generator, engine, anomaly detection and LLM tool endpoints. The browser is a pure renderer.

## D-017, Data package layout and reproducibility | 2026-10-10 | accepted
**Decision:** The generator lives in `data/plantdata/`, deterministic by seed (`python -m plantdata --seed 42`). Small outputs (layout, employees, tasks, transfer times, events, schedule) are committed in `data/out/`; large sensor files are Parquet, committed only if small, otherwise regenerated. Specification in `docs/DATA_SPEC.md`.

## D-018, Scenario library and output model for forecasting | 2026-10-10 | accepted
**Context:** To forecast, the data needs ideal outputs, realistic outputs, faulted outputs and a longer history, not only sensor streams.
**Decision:** Five scenarios (ideal, healthy_realistic, hero_timely_repair, hero_delayed_repair, hero_ignored) with sensors and per-minute production output, a serial-line output model (buffer upstream, derate and scrap when a weld robot degrades), and a 30-day history with incidents and remaining-useful-life labels. Downtime cost uses an assumed $20,000 per minute from the brief.
**Consequences:** The simulation engine must reproduce the same quantities (units, OEE, downtime) and can be sanity-checked against these scenario summaries. The cost figure must be cited with a real source before the pitch.
