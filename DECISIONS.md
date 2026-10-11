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

## D-013, Where the simulation engine lives | 2026-10-10 | open
**Options:** (a) Python + SimPy as a FastAPI service next to anomaly detection and the LLM backend, twin renders streamed state; (b) TypeScript in the browser (Web Worker), no backend needed for the visuals.
**Leaning:** (a) for batch what-if runs (compare baseline vs scenario) and one language with the ML code; keep a thin TS fallback that replays recorded state if the backend is down during the demo.
**Needs:** agreement with the teammate and the decision on who hosts the FastAPI app.

## D-014, Ownership of anomaly detection and synthetic data | 2026-10-10 | open
**Context:** The whiteboard does not show anomaly detection; the brief has it (Isolation Forest + SHAP). Both sides need synthetic data.
**Proposal:** M generates Data 1 (sensor streams with injected bearing-wear signatures, shifts, timings) and runs anomaly detection on the simulated stream; T generates Data 2 (manuals, logs, graph). Confirm with teammate.

## D-015, Brain work lives in `brain/` on its own branch | 2026-10-11 | accepted
**Context:** T side (knowledge base, RAG, LLM brain, chat) needs a place in the shared repo without touching twin/sim files owned by M.
**Decision:** All T-side work goes in `brain/`, developed on branch `brain-kb`, merged via PR after review by M. Twin/sim files are not edited from this branch except additive docs (this log, CLAUDE.md pointers).
**Consequences:** Few merge conflicts. Shared contract files (`docs/STATIONS.md`, interface contract in CLAUDE.md) still change only through new D-entries.

## D-016, Brain data, RAG design and stack are open | 2026-10-11 | open
**Context:** An early domain brief (`brain/docs/talk-to-your-plant-domain-brief.pdf`) proposed graph-anchored multimodal RAG, Neo4j, hybrid synthetic plus public data. It predates knowing the repo scope (fictional Voltline plant, `S01..S12`, `M01..M10`, hero `M05` bearing wear, graph path `symptom -> failure_mode -> component -> repair -> spare_part`).
**Decision:** None yet. Owner of T side is working out data, RAG and stack and will bring a proposal. The brief is input only; its ontology must be realigned to the repo IDs before use.
**Consequences:** No stack choice is implied. Unchecked items in the brief (Bosch line data, SECOM, NHTSA, CWRU/Paderborn official links, MVTec license) stay unverified.
