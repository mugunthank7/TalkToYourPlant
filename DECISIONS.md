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
