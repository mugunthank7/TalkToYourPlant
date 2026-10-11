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

## D-019, M's scope is the blue boxes only | 2026-10-10 | accepted
**Decision:** M owns Data 1 generation, simulation engine, live plant state, what-if scenarios, dashboard (KPIs, throughput forecast) and the live 3D window. Not M's: knowledge base, LLM, chat, voice/vision, anomaly detection (grey box, owner open; supersedes the anomaly-detection part of D-014). M only exposes the live plant state and what-if as an API so the LLM side can read them, and renders what it is sent (alerts, graph path).
**Consequences:** Data 1 files include ground-truth fault labels so whoever builds anomaly detection can train on them.

## D-020, Brain work lives in `brain/` on its own branch | 2026-10-11 | accepted
**Context:** T side (knowledge base, RAG, LLM brain, chat) needs a place in the shared repo without touching twin/sim files owned by M.
**Decision:** All T-side work goes in `brain/`, developed on branch `brain-kb`, merged via PR after review by M. Twin/sim files are not edited from this branch except additive docs (this log, CLAUDE.md pointers).
**Consequences:** Few merge conflicts. Shared contract files (`docs/STATIONS.md`, interface contract in CLAUDE.md) change only through new D-entries.

## D-021, Brain RAG design and stack are open | 2026-10-11 | open
**Context:** An early domain brief (`brain/docs/talk-to-your-plant-domain-brief.pdf`) proposed graph-anchored multimodal RAG, Neo4j, hybrid synthetic plus public data. It predates the repo scope.
**Decision:** None yet on stack. T owner brings a proposal. The brief is input only.
**Consequences:** No stack choice is implied.

## D-022, Twin IDs win; T's Voltara dataset is re-keyed to them | 2026-10-11 | accepted
**Context:** M's generator (Voltline: 10 to 11 machines `M01..M11`, 12 stations, 24 employees) and T's generator (Voltara: 119 machines, 452 employees, ~20k work orders, 83 SOPs/manuals, ~11k RAG chunks, graph seed) used different plant names and ID schemes, breaking D-008.
**Decision:** Voltline IDs (`M01..M11`, `S01..S12`, employee IDs) are final. T's data is re-keyed to them in `brain/data/` via `crosswalk_*.csv` and `build_keyed.py`. Nothing in `data/` or the twin changes. Mapped: M01 `CAS-GP-02`, M02 `STP-BLK-01`, M04 `BIW-WF-01`, M05 `BIW-WK-05`, M06 `GA-CV-01`, M07 `BIW-MET-01`, M08 `BAT-BS-01`, M09 `BAT-BT-01`, M11 `LOG-AM-01`. M03 framing fixture and M10 decoiler have no Voltara family and are added as synthetic stubs. The other ~108 Voltara machines are knowledge-base only (not rendered). Four twin staff (`A-TECH01`, `B-TECH01`, `A-SUP01`, `B-SUP01`) replace the matching people in M05's escalation chain.
**Consequences:** One ID space across 3D, sensor stream and graph. KB answers can cite the real plant breadth. The Voltara README's "Voltara Motors" name survives only in document text; the demo plant name remains Voltline EV Works (D-002) unless M and T agree otherwise.

## D-023, Hero M05 bearing wear is authored into the knowledge base | 2026-10-11 | accepted
**Context:** Voltara's catalog has no joint-bearing-wear fault mode for weld robots (its KUKA faults are gearbox oil leak, brake, RDC battery, tips, etc.), but the twin's hero scenario and interface contract need `vibration_high -> bearing_wear -> m05_joint1_bearing -> replace_bearing -> bearing_6208`.
**Decision:** Author the hero content as synthetic: fault mode `bearing_wear` on family WK, component nodes `m05_*` (10, from `docs/STATIONS.md`), repair `replace_bearing`, spare part `bearing_6208` (2 on hand, bin S12, lead time 9 days), SOP `SOP-MNT-M05-01`, a past-incident chunk on M04, sensor signal crosswalk (`vibration_rms` <-> `vibration_mm_s`, `temperature_c` <-> `motor_temp_c`, `motor_current_a`). Example `alert` and `graph_path` messages in `brain/data/hero_m05_messages.json` match the interface contract. Run-extension logic reuses existing `SOP-OPS-02`.
**Consequences:** The hero demo path works end to end in the KB. SHAP values in the example alert are illustrative until anomaly detection exists (owner open, see D-019). `BIW-WK-03` (Voltara's gearbox oil leak storyline) stays as a contrast case.

## D-024, Downtime cost $38,000 per minute (Siemens 2024) | 2026-10-10 | accepted
**Decision:** Replace the brief's unsourced $20,000 per minute with $38,000 per minute, derived from Siemens' "True Cost of Downtime 2024": $2.3M per hour for a large automotive plant. The older $22,000 per minute figure is from a 2006 survey and is not used. See docs/SOURCES.md.
**Consequences:** Pitch wording: "industry figure for a large automotive plant". Single-line numbers are likely conservative-to-high; the constant is configurable.

## D-025, Estimated maintenance and downtime history | 2026-10-10 | accepted
**Decision:** Generate a year of estimated work orders, downtime events and a failure-mode catalogue (data/plantdata/maintenance.py). Structured numbers for dashboards and forecasts are M's; free-text manuals and logs remain the teammate's Data 2. The failure-mode catalogue uses our component IDs so the teammate can reuse it for the graph.

## D-026, Generated brain dataset is committed | 2026-10-11 | accepted
**Context:** M and T both need to inspect the same generated data on GitHub. D-017 commits small outputs and regenerates large ones.
**Decision:** `brain/data/out/` (about 46 MB, 169 files, largest 20 MB) is committed on request of T so the whole team sees both datasets: M's in `data/out/`, T's in `brain/data/out/`. Source of truth stays the generators; outputs are deterministic (seed 42). (Renumbered from D-024 after M's D-024 and D-025.)
**Consequences:** Repo grows by about 10 MB compressed. If the data is regenerated with a new seed or schema, the diff will be large; prefer rebuilding only on schema changes.

## D-027, Gemini access via google-genai with client-side rate limiting | 2026-10-11 | accepted
**Context:** Free-tier Gemini quotas are low and change; sources disagree on exact numbers (RPM, RPD per model, and embeddings unconfirmed).
**Decision:** Brain uses `google-genai`. Key in `brain/.env` (gitignored), never committed. Model names in env vars (`MODEL_AGENT`, `MODEL_LITE`, `MODEL_FALLBACK`, `MODEL_EMBED`); verified against the key's model list by `brain/scripts/check_key.py`. `brain/app/ratelimit.py`: sliding-window RPM and persisted daily budget per role (agent/lite/embed), set below real quotas by default, plus exponential backoff with jitter on 429/5xx honouring server retry hints. Embeddings are cached to disk by chunk hash so reruns cost nothing.
**Consequences:** Quota errors degrade to waiting or the fallback model, not crashes. Limits must be re-checked on the AI Studio rate-limit page before demo day and set in `.env`.

## D-028, Gemini models: 3.8 Flash agent, 3.5 Flash-Lite cheap steps | 2026-10-11 | accepted
**Context:** `gemini-2.5-flash` returned 404 "no longer available to new users". `brain/scripts/check_key.py` listed the models this key can use.
**Decision:** Agent `gemini-3.8-flash`, cheap steps `gemini-3.5-flash-lite`, fallback `gemini-3.7-flash`, embeddings `gemini-embedding-001` (3072 dims). All set via env vars, so they can change without code edits. Client-side RPM/RPD defaults stay conservative because the free-tier limits for these models are not confirmed.
**Consequences:** Preview/latest model names can be retired; re-run `check_key.py` before the demo.

## D-029, Real free-tier quotas: agent on Flash-Lite, local embeddings | 2026-10-11 | accepted
**Context:** AI Studio usage page shows the project's actual limits: `gemini-3.8-flash` 5 RPM / **20 RPD**; `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` 15 RPM / 500 RPD, 250K TPM; other 3.x/2.5 Flash 5 RPM / 20 RPD; Gemini Embedding 100 RPM / **30K TPM** / 1K RPD. A tool-calling agent turn costs several requests, so 3.8 Flash would last only a handful of questions per day. Embedding ~11k chunks (~650k words) at 30K TPM needs 30+ minutes of quota and risks the daily cap.
**Decision:** Agent = `gemini-3.5-flash-lite`, cheap steps and fallback = `gemini-3.1-flash-lite` (quotas are per model, so fallback is a separate bucket). `gemini-3.8-flash` is a `premium` role reserved for the final hero-demo answer (client cap 16/day). Embeddings default to local `sentence-transformers/all-MiniLM-L6-v2` (already cached, no quota), with `EMBED_BACKEND=gemini` as option. Rate limiter now also enforces TPM. Eval scores retrieval without LLM calls and caches LLM answers to stay within 500 RPD.
**Consequences:** Demo quality of the final answer can use 3.8 Flash on the hero path only. If limits change, edit `brain/.env`. Local embeddings are lower quality than Gemini's; BM25 hybrid compensates.

## D-030, Knowledge graph: NetworkX, built deterministically, no LLM extraction | 2026-10-11 | accepted
**Context:** The dataset already ships a typed graph seed (5,694 nodes, 18,038 edges) plus hero nodes from D-023; the graph is small and must answer fast.
**Decision:** `brain/app/graph.py` loads `rag/graph_nodes.jsonl` + `graph_edges.jsonl` into a NetworkX `MultiDiGraph` (about 0.1 s) and enriches it from `master/*` and `logs/work_orders.jsonl`. API: `get_machine`, `neighbors`, `escalation_chain(machine, shift)`, `assigned_staff`, `fault_modes`, `recent_work_orders`, `repeat_failures`, `path_between`, `find_machines` (entity linking), `hero_graph_path` (twin contract message). Ids resolve loosely (`M05`, `BIW-WK-05`, `Giga Press 1`). Current shift is derived from the clock (A 06-14, B 14-22, C 22-06) unless passed.
**Consequences:** No Neo4j server, no LLM cost for graph building. Fault modes live at family level, so per-machine fault answers go machine -> family -> fault. Shortest path between hero nodes uses the shortcut `bearing_wear -NEEDS_PART-> bearing_6208`; the twin's 5-node path comes from `hero_graph_path()`. Tests: `python3 brain/tests/test_graph.py` (19 checks).

## D-031, Retrieval: local embeddings + BM25 hybrid, exact numpy search, no FAISS | 2026-10-11 | accepted
**Context:** 11,105 short chunks (about 430 chars). Gemini embedding quota is 30K TPM / 1K RPD (D-029). Importing `faiss` together with `sentence-transformers` segfaulted (exit 139) on this macOS setup.
**Decision:** `brain/app/index.py`: local `all-MiniLM-L6-v2` embeddings (11k chunks in about 70 s once, cached to `brain/.cache/` by chunk-text hash, reload 0.4 s) + BM25 (title weighted x2, fault codes and IDs tokenised whole and in parts), fused with reciprocal rank fusion. Exact inner-product search in numpy replaces FAISS (single matmul, about 30 ms per query incl. BM25). Metadata filters: machine (plus that machine's family manuals), doc_type, family, area, fault_code, shift. Deterministic query expansion maps phrasing like "keep running 2 more hours" onto SOP vocabulary (`SOP-OPS-02`), "who do I page" onto escalation docs; "shift A/B/C" in a query becomes a filter.
**Consequences:** No quota use for indexing. Pure dense retrieval missed SOP-OPS-02 for natural phrasing (not in top 10); expansion fixed it, so new intents need new expansion rules or the agent must pass `doc_type`. Gemini embeddings remain available via `EMBED_BACKEND=gemini`. Tests: `python3 brain/tests/test_index.py` (10 checks).
