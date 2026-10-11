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

## D-027, Compact layout, visible material flow, factory shell | 2026-10-10 | accepted
**Context:** The 160 x 90 m plant was too sparse to read in one glance, parts and cars appeared from nowhere, and the grey flat environment did not look like a plant.
**Decision:** (1) Compact plant to 128 x 72 m with the same station arrangement; layout and walkways regenerate from data/plantdata/layout.py. (2) Add `logistics` routes to layout.json (coil, stamped-parts, underbody, body, battery-pack AGVs, a pallet forklift, a spares cart) and animate them in twin/src/scene/Flow.tsx, all as pure functions of the sim clock. (3) Cars enter the belt on an underbody AGV and are built up along S04 to S07 (floor pan, frame, shell rises, paint, wheels), then leave on an AGV to S09. (4) Factory shell: light glossy floor, concrete and corrugated-steel walls with window band, columns, crane runways with a moving bridge crane, pendant fixtures, the hangar HDRI as blurred backdrop. (5) The 3D view is shifted so the plant sits between the HUD panels, so everything is visible at once.
**Consequences:** Station pads are now relatively small against the hall; the next pass builds richer per-station models (S11, S12, S10, S09, S02, S03 first).

## D-028, Station models are procedural React components, built from reference images | 2026-10-11 | accepted
**Context:** The user supplies ChatGPT reference images per station (prompts in docs/STATION_PROMPTS.md, images in docs/reference/) and wants a wow-factor look.
**Decision:** Build each station as an R3F component in twin/src/scene/stations/ from a shared kit (rounded boxes, glass, wire mesh, canvas screens, signs, static people). Screens show live data (video wall, andon board, EOL test, CMMS). Blender stays reserved for hero assets that need exact part names (weld robot) if the procedural look is not enough.
**Consequences:** Fast iteration and live-data screens, no GLB pipeline. Models stay low-to-medium poly; adaptive quality drops bloom and shadows on slow GPUs.

## D-029, Client-side plant state engine until SimPy exists | 2026-10-11 | accepted
**Decision:** Fault behaviour (stops, starving, blocking, repair, KPI impact) lives in twin/src/plant.ts as pure functions of the sim clock plus a list of injected faults. Scripted hero repair and injected faults share one interval model. The SimPy engine (D-016) replaces this later and must emit the same per-station states (run, fault, repair, starved, blocked).
**Consequences:** The demo can inject any fault on demand without a backend. KPI changes from injected faults are approximations (extra downtime added to the precomputed scenario series).

## D-030, The SimPy engine is the source of truth | 2026-10-11 | accepted
**Decision:** `sim/` implements D-016. Strict-pitch paced line with buffers, mid-job failures, a technician and work orders, replayable named random streams. What-if = replay to now, apply changes, run to the horizon, compare with the unchanged future (no state copying needed). `MICRO_X = 4.5` calibrates everyday OEE to the generated scenarios (tolerance 8 percent, tested). The client-side engine in plant.ts (D-029) stays as the offline fallback.
**Consequences:** KPIs and what-if numbers in the twin come from the engine when connected. The precomputed `kpi.json` series are still used for the dashboard charts; exporting them from the engine is a follow-up. Per-second accounting was replaced by lost-pitch accounting so that downtime, cost and lost cars agree.
**Open:** anomaly detection is still not implemented (alerts follow the scripted wear curve); the LLM side calls the tool endpoints.

## D-031, Real anomaly detector inside the engine | 2026-10-11 | accepted
**Context:** D-019 left anomaly detection without an owner and the engine alerted from the scripted wear curve. The user asked for real detection on the healthy and fault data.
**Decision:** Isolation Forest trained on healthy data only, on load-normalised features with a thermal-lag temperature model, exact Shapley explanations and conformal RUL intervals (docs/ANOMALY.md). The engine produces telemetry with the generator's dynamics and feeds a streaming monitor; the hero WO is triggered by the model's critical alert. Live mode monitors all machines, what-if replays monitor only M05. Supersedes the "M does not own anomaly detection" part of D-019.
**Consequences:** Alert time now depends on the model (3.4 h vs the scripted 5.1 h); tests assert zero false alerts and an alert before the 2x-vibration rule. `dispatch_now` expedites the already-open work order instead of opening a second one. Results are on synthetic data with injected signatures; the doc says so.

## D-032, Dashboard history is exported from the engine | 2026-10-11 | accepted
**Decision:** `python -m plantsim.export` (sim/) rewrites `kpi.json` (five scenarios, same seed as the live engine so the "repaired on alert" scenario is exactly the live run) and the shift history and incidents in `dashboard.json` (30 days, 52 shifts, 15 percent with an M05 wear incident, random failures on, Saturday takt 120 s, per-day efficiency, detector-raised alerts). Hero timings (alert, technician arrival, repair end) are written into the summary and used by the HUD timeline and jump buttons when the engine is connected.
**Consequences:** Dashboard numbers equal what the twin and the what-if show (tested). Limits: incidents are M05 wear only (the engine models one degradation curve); the 12-month maintenance statistics (MTBF, MTTR, downtime by cause, month and machine) remain generator estimates and are labelled as such. Rerun the export after changing the engine. The scripted `events.json` hero times are now only used offline.

## D-033, Gemini access via google-genai with client-side rate limiting | 2026-10-11 | accepted
**Context:** Free-tier Gemini quotas are low and change; sources disagree on exact numbers (RPM, RPD per model, and embeddings unconfirmed).
**Decision:** Brain uses `google-genai`. Key in `brain/.env` (gitignored), never committed. Model names in env vars (`MODEL_AGENT`, `MODEL_LITE`, `MODEL_FALLBACK`, `MODEL_EMBED`); verified against the key's model list by `brain/scripts/check_key.py`. `brain/app/ratelimit.py`: sliding-window RPM and persisted daily budget per role (agent/lite/embed), set below real quotas by default, plus exponential backoff with jitter on 429/5xx honouring server retry hints. Embeddings are cached to disk by chunk hash so reruns cost nothing.
**Consequences:** Quota errors degrade to waiting or the fallback model, not crashes. Limits must be re-checked on the AI Studio rate-limit page before demo day and set in `.env`.

## D-034, Gemini models: 3.8 Flash agent, 3.5 Flash-Lite cheap steps | 2026-10-11 | accepted
**Context:** `gemini-2.5-flash` returned 404 "no longer available to new users". `brain/scripts/check_key.py` listed the models this key can use.
**Decision:** Agent `gemini-3.8-flash`, cheap steps `gemini-3.5-flash-lite`, fallback `gemini-3.7-flash`, embeddings `gemini-embedding-001` (3072 dims). All set via env vars, so they can change without code edits. Client-side RPM/RPD defaults stay conservative because the free-tier limits for these models are not confirmed.
**Consequences:** Preview/latest model names can be retired; re-run `check_key.py` before the demo.

## D-035, Real free-tier quotas: agent on Flash-Lite, local embeddings | 2026-10-11 | accepted
**Context:** AI Studio usage page shows the project's actual limits: `gemini-3.8-flash` 5 RPM / **20 RPD**; `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` 15 RPM / 500 RPD, 250K TPM; other 3.x/2.5 Flash 5 RPM / 20 RPD; Gemini Embedding 100 RPM / **30K TPM** / 1K RPD. A tool-calling agent turn costs several requests, so 3.8 Flash would last only a handful of questions per day. Embedding ~11k chunks (~650k words) at 30K TPM needs 30+ minutes of quota and risks the daily cap.
**Decision:** Agent = `gemini-3.5-flash-lite`, cheap steps and fallback = `gemini-3.1-flash-lite` (quotas are per model, so fallback is a separate bucket). `gemini-3.8-flash` is a `premium` role reserved for the final hero-demo answer (client cap 16/day). Embeddings default to local `sentence-transformers/all-MiniLM-L6-v2` (already cached, no quota), with `EMBED_BACKEND=gemini` as option. Rate limiter now also enforces TPM. Eval scores retrieval without LLM calls and caches LLM answers to stay within 500 RPD.
**Consequences:** Demo quality of the final answer can use 3.8 Flash on the hero path only. If limits change, edit `brain/.env`. Local embeddings are lower quality than Gemini's; BM25 hybrid compensates.

## D-036, Knowledge graph: NetworkX, built deterministically, no LLM extraction | 2026-10-11 | accepted
**Context:** The dataset already ships a typed graph seed (5,694 nodes, 18,038 edges) plus hero nodes from D-023; the graph is small and must answer fast.
**Decision:** `brain/app/graph.py` loads `rag/graph_nodes.jsonl` + `graph_edges.jsonl` into a NetworkX `MultiDiGraph` (about 0.1 s) and enriches it from `master/*` and `logs/work_orders.jsonl`. API: `get_machine`, `neighbors`, `escalation_chain(machine, shift)`, `assigned_staff`, `fault_modes`, `recent_work_orders`, `repeat_failures`, `path_between`, `find_machines` (entity linking), `hero_graph_path` (twin contract message). Ids resolve loosely (`M05`, `BIW-WK-05`, `Giga Press 1`). Current shift is derived from the clock (A 06-14, B 14-22, C 22-06) unless passed.
**Consequences:** No Neo4j server, no LLM cost for graph building. Fault modes live at family level, so per-machine fault answers go machine -> family -> fault. Shortest path between hero nodes uses the shortcut `bearing_wear -NEEDS_PART-> bearing_6208`; the twin's 5-node path comes from `hero_graph_path()`. Tests: `python3 brain/tests/test_graph.py` (19 checks).

## D-037, Retrieval: local embeddings + BM25 hybrid, exact numpy search, no FAISS | 2026-10-11 | accepted
**Context:** 11,105 short chunks (about 430 chars). Gemini embedding quota is 30K TPM / 1K RPD (D-035). Importing `faiss` together with `sentence-transformers` segfaulted (exit 139) on this macOS setup.
**Decision:** `brain/app/index.py`: local `all-MiniLM-L6-v2` embeddings (11k chunks in about 70 s once, cached to `brain/.cache/` by chunk-text hash, reload 0.4 s) + BM25 (title weighted x2, fault codes and IDs tokenised whole and in parts), fused with reciprocal rank fusion. Exact inner-product search in numpy replaces FAISS (single matmul, about 30 ms per query incl. BM25). Metadata filters: machine (plus that machine's family manuals), doc_type, family, area, fault_code, shift. Deterministic query expansion maps phrasing like "keep running 2 more hours" onto SOP vocabulary (`SOP-OPS-02`), "who do I page" onto escalation docs; "shift A/B/C" in a query becomes a filter.
**Consequences:** No quota use for indexing. Pure dense retrieval missed SOP-OPS-02 for natural phrasing (not in top 10); expansion fixed it, so new intents need new expansion rules or the agent must pass `doc_type`. Gemini embeddings remain available via `EMBED_BACKEND=gemini`. Tests: `python3 brain/tests/test_index.py` (10 checks).

## D-038, Agent: plain Gemini tool loop, grounded citations, graceful degradation | 2026-10-11 | accepted
**Context:** T owns the LLM brain and chat. Quotas are tight (D-035) and the 3D twin must receive machine ids to highlight.
**Decision:** `brain/app/agent.py` is a manual function-calling loop on `google-genai` (no framework), up to 6 steps. Tools: `graph_lookup`, `escalation_chain`, `search_docs`, `get_sensor_state`, `run_scenario`, `create_work_order`, `highlight`. Output `{answer, highlight:{machine_ids, graph_path}, citations, actions, meta}`. Citations are only ids that were actually retrieved and appear in the answer text; `meta.sources_consulted` lists everything retrieved. Retrieved context is capped (600 chars per chunk, 5,000 per call). Answers are cached on disk by question, shift and recent history. Failure ladder: agent model -> fallback model (separate quota bucket) -> deterministic no-LLM answer from graph and retrieval, flagged `degraded`. `premium: true` runs the loop on `gemini-3.8-flash` (20 RPD). Highlight falls back to machines touched by tools; `graph_path` uses the twin's 5-node hero path for M05 bearing wear.
**Consequences:** One chat turn costs 2-4 requests of the 500/day agent budget. Mugu's engine is reached through `brain/app/sim_adapter.py`: `SIM_MODE=mock` (default; built from his `data/out/events.json` and `scenarios/summary.json`) or `live` (assumed `GET /state`, `POST /scenario`, `POST /work_order`; to be confirmed by M). Mock what-if only models M05; `failure_probability` is an estimate per matched scenario, labelled as such in the result.

## D-039, API and chat UI | 2026-10-11 | accepted
**Decision:** FastAPI in `brain/app/api.py` (`POST /chat`, `GET /health`, `GET /` serves `brain/ui/index.html`), CORS open for the twin. Single static page, no build step: message list, citation chips, highlighted-machine chips, graph path, actions, model/latency line. Run: `python3 brain/app/api.py` (port 8100, `BRAIN_PORT` to change).
**Consequences:** Mugu's 3D window consumes `highlight.machine_ids` and `highlight.graph_path` from the same response.

## D-040, Default LLM backend is local (Ollama) with a deterministic answer pipeline | 2026-10-11 | accepted
**Context:** Hosted Gemini cost money and was unreliable: a full eval hit `402 RESOURCE_EXHAUSTED: prepayment credits are depleted` mid-run (D-035 quotas), and each chat turn spent 2-4 requests. T asked to switch to a local LLM. Machine: M2, 8 GB RAM, Ollama installed with `qwen2.5:7b`, `qwen2.5vl:3b`, `gemma2:2b`, `llama3.1:8b`, etc.
**Measured:** local models composing answers from tool results took 33-77 s per answer and made errors: `qwen2.5:7b` invented people ("John Doe") for a keep-running question and mislabelled an L1 level; `qwen2.5vl:3b` answered "Not applicable"; `gemma2:2b` was weak and slow.
**Decision:** `LLM_BACKEND=ollama` is the default. In this mode `brain/app/agent.py` uses a deterministic pipeline: regex/entity intent router (page, keep-running, repeats, fault code/parts, SOP, work order, status/why-red) -> the same tools -> intent-specific renderers that write the answer straight from tool results with verified `[id]` citations. No LLM call for these intents (0-8 s, free, cannot hallucinate). Only questions the router cannot classify go to local `qwen2.5:7b` with the tool results as sole context. `LOCAL_NARRATE=1` forces LLM phrasing; `LLM_BACKEND=gemini` restores the Gemini tool-calling loop. RAGAS judging still needs Gemini (the local judge is too slow and unreliable here).
**Consequences:** Cost is zero and answers for supported intents are faithful by construction. Trade-off: new phrasings or intents need router rules; free-form questions get weaker, slower local answers. Eval on the local pipeline: 40/40 pass in 2 s (note: the questions were generated from the same data and intents the router was written for, so this measures grounding and routing, not open-ended robustness). Hero fault gained three `CAUSED_BY` causes in `build_keyed.py`.

## D-041, Evaluation: results and RAGAS status | 2026-10-11 | accepted
**Context:** `brain/eval/questions.jsonl` (40 questions with gold from the data), `run_eval.py` (retrieval hit@6/MRR and end-to-end checks), `run_ragas.py` (faithfulness, answer relevancy, context precision/recall; isolated `brain/.venv-ragas`, Gemini as judge).
**Results:** retrieval hit@6 0.96, MRR 0.86 (one miss: LSR-PWR-LOW). Gemini agent: 37/40, then 40/40, then 39/40 on repeat runs (citation omissions); one run was cut short by the 402 above. Local pipeline: 40/40. RAGAS ran on 6 of 20 questions before being stopped (first rows: faithfulness 0.85, answer relevancy 0.88-0.89, context precision 1.0, context recall 1.0); no full RAGAS summary exists yet.
**Decision:** Keep RAGAS as an optional, paid-judge step; do not treat the partial rows as a result. Run it when quota/credits allow: `brain/.venv-ragas/bin/python brain/eval/run_ragas.py --every 2`.
**Consequences:** Eval numbers in this log are from different backends; compare like with like.

## D-042, Gemini removed completely; everything runs locally | 2026-10-11 | accepted (supersedes D-033, D-034, D-035 and the Gemini loop in D-038)
**Context:** Hosted Gemini cost money, hit `402 prepayment credits depleted`, and needed a key (the key had also been pasted into chat). T asked for local models only.
**Decision:** Removed `brain/app/ratelimit.py`, `brain/scripts/check_key.py`, the Gemini tool-calling loop, Gemini embeddings, all key/model/quota config and the `google-genai` dependency. `brain/.env` no longer holds any key. LLM = local Ollama (`OLLAMA_MODEL`, used only for questions the intent router cannot template, D-040). Embeddings = local sentence-transformers. RAGAS judge = local Ollama.
**Consequences:** No cost, no quota, no network. The previously pasted API key should be deleted in AI Studio. Eval numbers from the Gemini era in D-041 are historical.

## D-043, Embedding experiment and default embedder | 2026-10-11 | accepted
**Context:** Retrieval quality depends on the dense model; MiniLM was the first pick for speed and being already cached. `brain/eval/embed_experiment.py` compares 5 local models on 23 scoped data questions ("gold") and 20 unscoped natural paraphrases ("para"), each as dense only, BM25 only and hybrid (RRF); `embed_sweep.py` varies the fusion weights. Results: `brain/eval/embed_experiment.json`, shown on the dashboard.
**Results (hit@6 gold / para, hybrid 1:1):** all-MiniLM-L6-v2 0.96 / 0.60; bge-small-en-v1.5 1.00 / 0.70; e5-small-v2 0.91 / 0.80; all-mpnet-base-v2 1.00 / 0.75; nomic-embed-text (Ollama) 0.83 / 0.65. BM25 alone scores 0.91 / 0.75 on every model (query terms such as fault codes and ids), so a weak dense model drags hybrid below BM25 on paraphrases (MiniLM, nomic). Raising the BM25 weight trades scoped accuracy for paraphrases (bge: 1.00 / 0.70 at 1:1 versus 0.91 / 0.75 at 1:2). Build time for 11,105 chunks: MiniLM 70 s, bge 151 s, e5 177 s, nomic 357 s, mpnet 509 s on the M2. Query latency 57-188 ms.
**Decision:** Default `LOCAL_EMBED_MODEL=BAAI/bge-small-en-v1.5` with equal fusion weights. Agent retrieval is machine-scoped whenever the machine is known, where bge is perfect; e5-small is the better choice for unscoped free text.
**Consequences:** Retrieval eval improved from hit@6 0.96 / MRR 0.86 to 1.00 / 0.93; index tests pass. Caveat: 23 and 20 queries are small, so differences under about 10 points are noise; nomic's weak result may partly come from truncation or prefix handling in Ollama and was not investigated.

## D-044, RAGAS with a local judge: own implementation of the metric definitions | 2026-10-11 | accepted
**Context:** The ragas library (0.4.3) with a local Ollama judge stalled at 0% CPU for 8+ minutes on one question (`qwen2.5:7b`, 8 GB M2) and the machine then thrashed (load average 57, heavy swap) until I killed it. Qwen 7B is too big to run next to the rest of the stack on this machine.
**Decision:** `brain/eval/run_ragas.py` re-implements the four RAGAS metrics with the same definitions and direct Ollama calls (JSON mode): faithfulness (statements supported by contexts / statements), answer relevancy (cosine of the question to 3 questions generated from the answer, local embeddings), context precision (average precision of useful contexts against the reference) and context recall (reference sentences attributable to contexts). Judge `phi3:3.8b` (about 50 s per question for all four metrics). Contexts are the tool outputs the brain saw (1,400 chars each, max 6). The library runner is kept as `run_ragas_lib.py`, unused. Judged by a 3.8B model, so scores are indicative; they are not comparable with RAGAS numbers from GPT-class judges.
**Consequences:** Run all 40 questions in about 30-40 minutes. A first pass with 600-char contexts under-scored (faithfulness 0.4, recall 0.0 on a fully grounded answer) because the escalation names were cut off; with 1,400 chars the same question scored 1.0 / 1.0, so context truncation is part of the measurement, not noise.

## D-045, Run dashboard | 2026-10-11 | accepted
**Decision:** `brain/app/dashboard.py` (port 8200) with `brain/ui/dashboard.html` shows live status of the eval, RAGAS and embedding-experiment jobs (progress, ETA, log tail, partial metrics, per-question results, embedding comparison) and can start or stop them, one heavy job at a time. Jobs write `brain/eval/status/<job>.json` (gitignored).

## D-046, RAGAS results (local judge phi3:3.8b, 40 questions) and two measurement fixes | 2026-10-11 | accepted
**Context:** First full run (41 min) produced impossible values: context recall 2.0 on three storyline questions and faithfulness 1.17 on one, because the judge returned more verdicts than statements and my code divided the raw count. Five faithfulness scores were missing (judge returned invalid JSON). Separately, a parts question (Q39) scored faithfulness 0.11 and recall 0.0 on a correct answer: the fault-mode tool output was truncated at 1,400 chars and the relevant `bearing_wear` mode sat at the end of the list.
**Fixes:** verdicts are now de-duplicated by index, restricted to valid indices and capped at 1.0; `graph_lookup fault_modes` puts the requested fault code first (router passes the code, or `bearing_wear` for M05) so truncation cannot hide it. 25 affected rows were re-scored (`run_ragas.py --ids`). Pipeline cache key bumped to `render-v3`.
**Final results:** faithfulness 0.888 (35 of 40 scored), answer relevancy 0.784 (39/40), context precision 1.000, context recall 0.975. By category (faithfulness / relevancy): who_to_page 0.94 / 0.77, fault_code 0.90 / 0.81, parts 0.92 / 0.81, hero 0.89 / 0.76, storyline 0.93 / 0.82, repeat_failure 0.83 / 0.87, sop 0.82 / 0.80, keep_running 0.76 / 0.59 (lowest). No score below 0.5 remains. Eval pass rate 40/40; retrieval hit@6 1.00, MRR 0.93.
**Caveats:** (1) the judge is a 3.8B model, so scores are indicative; (2) context precision of 1.0 is partly by construction, since the contexts are the tool outputs the pipeline chose for the intent; (3) answer relevancy is low for templated answers because it measures how question-like the generated questions are, not correctness; (4) 5 faithfulness scores are missing, not zero; (5) the weakest area is keep-running answers (long scenario text, few claims the judge can match to context).
**Consequences:** Results are in `brain/eval/ragas_latest.json` and on the dashboard. Next improvement candidates: shorter keep-running answers, a stronger judge if memory allows, retry on invalid judge JSON.

## D-047, Brain connects to M's SimPy engine through its /tools API | 2026-10-11 | accepted
**Context:** M's engine (D-030, D-031) exposes `POST /tools/{name}` with `get_machine_health`, `get_anomaly_report`, `get_diagnosis_context`, `run_what_if`, `create_work_order`. The brain's earlier endpoint guesses (`/state`, `/scenario`, `/work_order`) did not match.
**Decision:** `LiveSim` in `brain/app/sim_adapter.py` maps those tools to the brain's sensor, scenario and work-order calls; anomaly contributors, RUL and the engine's own what-if summary pass through. Unsimulated machines fall back to mock storyline data. The answer cache key now includes `SIM_MODE`.
**Consequences:** Real SHAP contributors and RUL from M's detector replace the illustrative ones once live. Not yet run against the real engine: its `anomaly.joblib` needs a newer numpy than this machine has and `pip` had no network, so verification used a stub with the shapes read from `sim/plantsim/tools.py`. Throughput is derived as units / 8 h; failure probability is shown as not modelled.

## D-048, Engine runs from its own venv; brain verified live against it | 2026-10-11 | accepted
**Context:** M's saved anomaly model (`sim/models/anomaly.joblib`) was pickled with numpy 2.x and scikit-learn 1.9.1. Loading it under the brain's numpy 1.26 / sklearn 1.3 failed in three layers: BitGenerator pickle form, `numpy._core` module path, then `GradientBoostingRegressor` loss objects (`'AbsoluteError' object has no attribute 'get_init_raw_predictions'`). Shimming the first two was not enough. A single `pip install -r sim/requirements.txt` also failed with DNS errors on this network; installing package by package worked.
**Decision:** The engine runs from `sim/.venv` (numpy 2.4.6, scikit-learn 1.9.1) and the brain keeps its own environment; they talk over HTTP only. `brain/scripts/start_all.sh` / `stop_all.sh` start and stop engine (:8000), brain chat API (:8100, `SIM_MODE=live`), run dashboard (:8200) and monitor (:8300). Answers are never cached in live mode (a cached answer from a stub run was served as if live before this was fixed).
**Verification (real engine, t=12,500 s, just after the hero alert):** why-is-M05-red returns real SHAP contributors and RUL (about 157 min); keep-running-2h uses the engine's what-if branch; an injected M03 fault stops S04, and the brain reports affected stations and the work order. Full eval in live mode: 40/40 in 42 s, retrieval hit@6 1.00 (`brain/eval/results_live.json`). Note the eval's "create work order" question opens a real work order in the running engine.
**Consequences:** `LiveSim` now calls `get_diagnosis_context` for evidence, affected stations, open work orders and the engine's own failure-mode candidates. The keep-running recommendation now compares engine cost and RUL interval with the SOP-OPS-02 limit instead of the mock thresholds: the engine can show lower downtime for a 2 h extension while SOP-OPS-02 still caps a rising trend at the current batch, and the answer says so.

## D-049, Integration monitor website | 2026-10-11 | accepted
**Decision:** `brain/app/monitor.py` + `brain/ui/monitor.html` (port 8300) poll the engine every 2 s and show OEE, throughput, M05 vibration and RUL, downtime cost with event markers; an event feed (alerts, machine state changes, stopped stations, work orders); the brain's automatic answer to each new alert or fault (latency, tools, highlight, citations, degraded flag); Inject fault / Clear faults / Ask buttons; and a baseline-versus-now impact table.
**Consequences:** One place to see how an injected failure propagates through the plant and how the brain responds. The monitor only reads the engine and the brain; it does not change either, except through the buttons.

## D-050, Click a station: station briefing API and 3D panel | 2026-10-11 | accepted
**Context:** The intended interaction is: a station blinks red, the user clicks it, and everything shown is about that station: what went wrong (sensors, alert, SHAP, affected stations, work orders), what to do, and the LLM's advice. The twin had no station selection and its chat button was a placeholder.
**Decision:** Brain: `brain/data/build_stations.py` builds `stations.json` and RAG chunks (what each station does, flow, machines, and the simulated failure modes per machine from M's `failure_modes.csv`); `brain/app/stations.py` and endpoints `GET /station/{id}`, `POST /station/{id}/plan` (local LLM, on demand), `POST /station/{id}/simulate`; `POST /chat` accepts `station_id` as focus. Twin (additive edits to M's files, for M to review): `selectedStation` in `state.ts`, click target and outline in `scene/Plant.tsx`, new `ui/StationPanel.tsx` and `brain.ts`, the placeholder chat button in `ui/Hud.tsx` replaced by a working chat, styles. The brain's live lookups now read one cached `/state` snapshot instead of per-machine tool calls: `get_diagnosis_context` runs two what-if branches each, which made the station endpoint hang while the engine was playing.
**Consequences:** Station briefings answer in about 0.4 s once warm (11 s cold). The deterministic steps are instant and grounded; the LLM plan is optional because a 7B model on 8 GB takes 30 to 70 s. Engine-side failure injection is by machine (`POST /fault`), not by failure mode, so the catalogue lists the modes but the simulate button breaks the machine generically.

## D-051, One structured answer format: status card with fixed sections | 2026-10-11 | accepted
**Context:** Answers were long field dumps (every sensor reading, mixed in one list), hard to read at a glance in the panel and in chat.
**Decision:** Every covered intent returns a card: title and severity, one-line headline, then WHAT HAPPENED, IMPACT, DO NOW (numbered, verb-first), WHO TO PAGE, PART, PROCEDURE and Sources; empty sections are omitted. The same content is returned as a `report` object next to `answer`, and the station panel renders it directly. The local LLM plan prompt requests the same sections. Built in `Brain._report` / `_card` in `brain/app/agent.py`; the old renderer remains as fallback.
**Consequences:** Short, scannable, grounded in tool results; citations still verified against retrieved ids. Eval unchanged: 40/40 in mock and live mode. Unclassified questions still return retrieved passages (`report: null`).

## D-052, Confidence-aware plain answers instead of retrieval dumps | 2026-10-11 | accepted
**Context:** Questions outside the intent router returned cleaned-up but raw passages (a shift-handover line for "how many cars yesterday", an SOP "Records" paragraph for "safety rules"), which looked machine-made and sometimes answered a different question. A stale session focus also pinned unrelated questions to the last machine.
**Decision:** `Brain._fallback` gives every uncovered question a short, direct answer and a `confidence` object. Handled without retrieval: greetings and capability questions, off-topic, unknown machine ids, a glossary, unknown areas (lists this plant's line), purchase requests, the andon. Handled with live engine data: output and OEE ("how many cars"), hypothetical stops ("what happens if the conveyor stops" runs the engine's inject-fault branch). From records: the best passage's one or two most relevant sentences, named by source id, with a relevance gate (term overlap, or strong semantic and keyword agreement) so an unrelated passage is refused rather than quoted. Session focus is only inherited for real follow-ups ("what should I do?", "who do I page?"). The 'safety' query expansion no longer matches the substring inside "happens" and is skipped for high-voltage questions.
**Consequences:** Eval stays 40/40 in mock and live mode. Fourteen demo prompts, including the awkward ones, give short natural replies; no answer uses model-disclaimer phrasing. Remaining gaps: questions about schedules ("when is the next maintenance for the press") and appearance ("what colour is the robot") get an honest "not in the plant records" plus suggestions.

## D-053, Verified demo question set, page guide and handoff docs | 2026-10-11 | accepted
**Decision:** `brain/eval/demo_questions.json` holds 18 questions in three groups (the M05 hero moment, what-if breakages, knowing the plant) with expected content; `brain/eval/demo_check.py [--reset]` runs them against the live stack and fails unless each is high confidence, not degraded and contains its expected text. `brain/docs/DEMO_QUESTIONS.md` (generated from a real run, with a 90-second path and questions to avoid), `brain/docs/PAGES.md` (what each web page does) and `brain/docs/HANDOFF.md` (files changed outside `brain/`, how to run and extend, open work in priority order) are the entry points for M. `CLAUDE.md` gained a Brain section.
**Consequences:** 18/18 high confidence on the live engine. The demo set depends on engine time 12,500 s; `--reset` rewinds to it.

## D-055, What-ifs run in worker processes; state broadcasts are throttled | 2026-10-11 | accepted
**Context:** Running the teammate's brain against the engine showed `run_what_if` taking 56 to 60 s with browser clients connected (7.7 s alone). The branches ran inside the API process and fought the event loop (state broadcast at 10 Hz to every client, JSON-encoded once per client).
**Decision:** `what_if_fast` runs the baseline and scenario branches in two spawned worker processes in parallel (falls back to in-process); state messages go out at 5 Hz while playing and 1 Hz while paused, encoded once. Export and tests still use the plain `what_if`.
**Consequences:** A what-if costs about the time of one branch (4.7 s measured on a quiet machine; 25 to 30 s when the Mac is saturated by rendering). First call pays about 2 s of worker start-up.

## D-054, Optional LLM layer with strict system prompts and a grounding guard | 2026-10-11 | accepted
**Context:** T's laptop cannot run a local LLM; M's can. The deterministic pipeline is grounded but reads like a template. Replies should be able to sound natural on a capable machine without ever becoming ungrounded.
**Decision:** `LLM_MODE=off` (default) keeps deterministic answers. `LLM_MODE=assist` gives the deterministic facts (card + tool results, or the top retrieved passages) to a local Ollama model with the prompts in `brain/app/prompts.py`: persona, grounding rules, style rules, JSON output contract, one fictional worked example (so a copied example is caught). `validate_reply` rejects replies that are empty or long, use disclaimer language, cite ids that were not retrieved, contain numbers of two or more digits absent from the facts or question, or use markdown; on rejection the deterministic answer is shown. Two consecutive failures pause the layer for 5 minutes. `OLLAMA_MODEL=auto` picks the best installed model from `MODEL_PREFERENCE` (32B, 14B, 8B, 7B, ...). Deterministic-only intents (greeting, glossary, unknown machine, off-topic, purchase request) never call the model. The station plan button uses the same prompt family. `brain/scripts/llm_check.py` and `brain/docs/LLM.md` explain how to try a model and read the guard.
**Consequences:** Switching models can improve wording but not grounding. Measured so far: guard unit checks pass; on this 8 GB laptop `qwen2.5:7b` timed out (fallback worked); `qwen3:0.6b` produced one accepted grounded reply and one rejected reply (cited an id from the old example, which is why the example is now fictional). Reply quality with a 14B+ model has not been measured: run `llm_check.py` on M's laptop and record the acceptance rate here.

## D-056, HUD v3: scene first, one panel at a time | 2026-10-11 | accepted
**Context:** The live view had eight always-open cards (state list, KPIs, cameras, fault simulator, forecast, timeline, what-if, chat) plus the station panel; they overlapped each other and covered most of the 3D scene.
**Decision:** Top-left KPI strip and one status banner (the single place for alerts and faults). Left rail with 12 live station dots and four tools (stations, cameras, fault simulator, forecast and what-if), each opening one drawer at a time. Right dock with Station and Ask tabs (the brain's station briefing and chat share one panel; chat answers show the same structured card). Bottom time dock with play, scrubber with event bands, speed and jump chips. One glass style, `twin/src/hud.css` (all rules under `.h3`). Dead CSS from the old cards was removed from `styles.css`.
**Consequences:** `StationPanel.tsx` (brain side) was restructured: same data and endpoints, new layout, plus the chat moved into it from `Hud.tsx`. Chat answers no longer switch the dock to the Station tab. The Dashboard tab is unchanged.

## D-057, "Explain the process" intent in the brain | 2026-10-11 | accepted
**Context:** Asking "explain the production process" in the twin's chat returned "No specific record found": the deterministic router had no overview intent, and the chat view dropped the fallback's suggestions.
**Decision:** New `process` intent in `brain/app/agent.py` (router, report card and plain render) that walks the stations in line order (S01 to S09, from `stations.json`) with the takt and the three support areas. Chat reports now show their suggestion chips and a numbered flow. Added to the demo set (19 questions).
**Consequences:** Small edit in the teammate's agent file; they should keep the branch when they extend `_route`. Any other open-ended "explain X" question still falls back until it gets its own intent.

## D-058, Only cite an SOP that applies to the machine | 2026-10-11 | accepted
**Context:** The status card for a stopped weld robot (M04) told the operator to "Follow SOP-SAF-03", which is the battery thermal event and fire response SOP. The card took the first SOP the search returned.
**Decision:** An SOP is cited for a machine only if it is written for that machine, for that machine's area, or is lockout/tagout (SOP-SAF-01). If none was retrieved, fall back to the area SOP (for example SOP-AREA-BIW). Cards show the SOP title next to its id.
**Consequences:** A wrong-but-plausible citation is worse than none, so a machine without a matching SOP gets no procedure line. Retrieval ranks by text similarity only, so any new place that picks a document from search results should apply the same applicability check.

## D-059, The knowledge-graph path is drawn on the plant | 2026-10-11 | accepted
**Context:** Chat answers carry `highlight.graph_path` (symptom, failure mode, component, repair, spare part) but the twin only selected one station.
**Decision:** `twin/src/graphpath.ts` places each node where it lives in the plant: symptom, failure mode and component stacked above the machine, the repair at the maintenance bay (S10), the spare part at the spares cage (S12), procedures at the control room (S11). `scene/GraphPath.tsx` reveals the nodes one by one with ground rings, beams and labels, arcs a line to the next node and keeps a pulse travelling along the chain. The camera frames the whole chain, offset clear of the right dock. Answers with only a machine light that machine. The Ask tab has "Show the path on the plant" and "Hide" buttons; closing the dock clears it.
**Consequences:** Only the M05 story has a full path today (the brain builds paths from its failure catalogue for M05); other machines show a single machine highlight until their paths exist. Node positions are by kind, so new node kinds need an entry in `anchorsFor`.
