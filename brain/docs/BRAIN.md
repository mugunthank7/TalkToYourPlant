# Brain (T side): knowledge graph, hybrid RAG, local-only agent, chat API, run dashboard

Fictional EV plant digital twin. The brain answers plant questions from tool results only, and tells the 3D twin which machines to highlight.

## Architecture (local only: no hosted LLM, no API key)
```
question -> Brain.ask (brain/app/agent.py)
   intent router (regex + entity linking) -> tools -> deterministic renderer     ~instant, cannot hallucinate
   unmatched question -> local Ollama model with the tool results as sole context  (30-70 s on 8 GB M2)
tools: graph_lookup / escalation_chain -> PlantGraph (NetworkX, 5.7k nodes)       brain/app/graph.py
       search_docs                      -> DocIndex (local embeddings + BM25, RRF)  brain/app/index.py
       get_sensor_state / run_scenario / create_work_order -> SimAdapter           brain/app/sim_adapter.py
       highlight                        -> machine ids + graph path for the twin
-> {answer, highlight, citations, actions, meta}   FastAPI chat service            brain/app/api.py   :8100
run dashboard (eval, RAGAS, embedding experiment)                                  brain/app/dashboard.py :8200
```
Data: `brain/data/out/` (built by `brain/data/build_keyed.py`; Voltara dataset re-keyed to the twin's `M01..M11` ids, D-022).

## Run
```
pip install -r brain/requirements.txt
python3 brain/data/build_keyed.py       # only if brain/data/out is missing
python3 brain/app/api.py                # chat UI + POST /chat on http://localhost:8100
python3 brain/app/dashboard.py          # run dashboard on http://localhost:8200 (start/stop eval, RAGAS, embeddings)
python3 brain/tests/test_graph.py && python3 brain/tests/test_index.py
```
RAGAS needs its own venv and a judge model: see the header of `brain/eval/run_ragas.py` and `brain/eval/Modelfile.judge`.

## Environment (brain/.env, all optional)
| var | default | meaning |
|---|---|---|
| `OLLAMA_URL` / `OLLAMA_MODEL` / `OLLAMA_NUM_CTX` | http://localhost:11434 / qwen2.5:7b / 6144 | local model for open-ended questions |
| `JUDGE_MODEL` | qwen2.5:7b (use `qwen-judge`, 8k ctx) | RAGAS judge |
| `LOCAL_EMBED_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | retrieval embeddings (see embedding experiment) |
| `LOCAL_NARRATE` | 0 | `1` makes the local LLM phrase every answer (slow, can hallucinate) |
| `SIM_MODE` / `SIM_URL` | mock / http://localhost:8000 | M's engine |
| `BRAIN_PORT` / `DASH_PORT` | 8100 / 8200 | ports |

## Answer format (every answer follows it)
`answer` is a plain-text card; `report` carries the same content as fields so a UI can lay it out:
```
M05 Weld robot 2 (station S06)  |  CRITICAL        <- title | severity (CRITICAL, WARNING, OK, INFO)
Needs action now.                                   <- one-line headline

WHAT HAPPENED   short facts: cause, the number that shows it, why it was flagged
IMPACT          minutes of life left, affected stations, cost per minute, open work orders
DO NOW          numbered, verb-first steps (who, what, which part)
WHO TO PAGE     L1, L2, L3 with name, extension, and when to escalate
PART            part number and stock
PROCEDURE       SOP id
Sources: [SOP-MNT-M05-01] [M05-A]                   <- ids that were actually retrieved
```
`report` = `{title, severity, headline, what_happened[], impact[], do_now[], contacts[], parts[], procedure[], sources[], intent}`. Sections with nothing to say are omitted. Covered intents: status/why-red, keep-running, who-to-page, fault code and parts, repeat failures, procedures, work order. Anything else falls back to retrieved passages and has `report: null`. The click-a-station panel renders `report` directly; the local LLM plan uses the same three sections.

## When there is no card: confidence and plain answers
Every response carries `confidence: {level: high|medium|low, score, reason}`. If no structured card applies, `Brain._fallback` answers in plain sentences and never in disclaimer language:
- **Small talk and scope:** greeting, thanks, "what can you do", off-topic questions, unknown machine ids (lists the real ones).
- **Direct answers without retrieval:** glossary (OEE, MTBF, MTTR, RUL, SHAP, andon, takt, LOTO, BOM, RCA, PM), "no such area in this plant" (lists the line), purchase requests (what it cannot do, plus stock and lead time).
- **Live numbers:** output and OEE from the engine; what-if "what happens if the conveyor stops" runs the engine's fault branch.
- **From the records:** best passage, cleaned of markup and trimmed to one or two sentences, named by source ("From SOP-SAF-04, ..."). High confidence states it; medium says "The closest thing I have is ..." and asks which machine or station; low says what it does not have and offers three questions to try.
Confidence comes from keyword match (BM25) and semantic similarity of the best passage and whether the passage shares terms with the question.

## Chat API
`POST /chat` `{message, session_id?, shift?}` returns:
```jsonc
{
  "answer": "the plain-text card above (citations as [DOC-ID])",
  "report": { "severity": "critical", "headline": "...", "do_now": ["..."] },   // structured version of the card, or null
  "highlight": {
    "machine_ids": ["M05"],                       // twin machine ids (or Voltara ids for non-rendered machines)
    "graph_path": [{"id":"vibration_high","kind":"symptom"}, {"id":"bearing_wear","kind":"failure_mode"},
                   {"id":"m05_joint1_bearing","kind":"component"}, {"id":"replace_bearing","kind":"repair"},
                   {"id":"bearing_6208","kind":"spare_part"}]   // same shape as the twin's graph_path message
  },
  "citations": [{"id":"SOP-MNT-M05-01", "excerpt":"..."}],   // only ids that were retrieved AND appear in the answer
  "actions": [{"type":"create_work_order","work_order":{"type":"work_order","id":"WO-1042","machine_id":"M05",...}},
              {"type":"run_scenario","machine_id":"M05","hours":2,"result":{"type":"scenario_result",...}}],
  "meta": {"model","degraded","error","llm_calls","contexts","sources_consulted","tools","shift","sim_mode","latency_s","cached"}   // model is "local-pipeline" or "ollama:<model>"
}
```
`GET /health` reports graph size, models, sim mode, key presence and today's usage per role.

## Tools given to the model
| tool | purpose |
|---|---|
| `graph_lookup(entity, what, shift?, fault_code?, target?, n?)` | machine, neighbors, fault_modes, staff, work_orders, repeats, path |
| `escalation_chain(machine_id, shift?)` | who to page: L0 to L3, engineers, vendor, timers; defaults to the current shift (A 06-14, B 14-22, C 22-06) |
| `search_docs(query, machine_id?, doc_type?, fault_code?, k?)` | hybrid retrieval over SOPs, manuals, work orders, RCA, logs; machine scope also returns that family's manual and plant SOPs |
| `get_sensor_state(machine_id)` | readings, status, alert with SHAP contributors |
| `run_scenario(machine_id, hours, op="keep_running")` | what-if via the simulator |
| `create_work_order(machine_id, component_id?, spare_part?, fault_code?, priority?, note?)` | only when the user asks |
| `highlight(machine_ids, graph_path?)` | tells the twin what to light up |

## Failure handling
If Ollama is down or errors, the brain answers in degraded mode straight from the graph and retrieval (flagged `degraded`). Answers are cached by question, shift and pipeline version.

## Connecting to M's engine (SIM_MODE=live)
`LiveSim` in `brain/app/sim_adapter.py` uses the engine's `/tools`: `get_diagnosis_context` (sensors, evidence, affected stations, open work orders, candidate failure modes, anomaly alert with SHAP contributors and RUL interval), `get_anomaly_report`, `run_what_if`, `create_work_order`. Machines the engine does not simulate (all except `M01..M10`) fall back to the mock storyline data. Answers are never cached in live mode.

**Verified end to end** against the real engine on this machine: why-is-M05-red (real SHAP contributors, RUL 157 min), keep-running-2h (engine branch: baseline vs scenario), injected fault on M03 (S04 stops, brain explains with affected stations and the work order).

### Run everything
```
python3 -m venv sim/.venv                       # engine venv (needs numpy 2 / scikit-learn 1.9 to read its saved model)
for p in simpy numpy pandas scipy scikit-learn joblib fastapi "uvicorn[standard]" websockets pyarrow httpx matplotlib pytest; do sim/.venv/bin/pip install "$p"; done
brain/scripts/start_all.sh                      # :8000 engine, :8100 brain, :8200 runs, :8300 monitor
brain/scripts/stop_all.sh
```
Dependency notes: the engine's `anomaly.joblib` was pickled with numpy 2.x / scikit-learn 1.9.1; loading it with numpy 1.26 / sklearn 1.3 fails (BitGenerator, `numpy._core`, then `AbsoluteError`), so the engine runs from its own `sim/.venv`. A single bulk `pip install -r` failed with DNS errors on this network; installing package by package worked. The brain itself keeps the older numpy; the two never share an environment.

### Click a station (3D twin, http://localhost:5180)
Click any station in the 3D scene: it gets a cyan outline and a panel opens (`twin/src/ui/StationPanel.tsx`) driven by the brain:
`GET /station/{id}` returns what the station does, live engine state and reason, each machine's sensors, alert, RUL and SHAP contributors, affected stations, open work orders, the recommended steps, who to page, the brain's diagnosis with citations, and the failure modes the simulator can inject there. `POST /station/{id}/plan` asks the local LLM for a short action plan from those facts (slow, on demand). `POST /station/{id}/simulate` injects a fault on that station's machine. The "Ask your plant" chat sends the selected station as context (`station_id`), so "what should I do?" refers to it, and answers select the station of the first highlighted machine.
Station and failure knowledge (`brain/data/out/stations.json`, plus RAG chunks) is built by `brain/data/build_stations.py` from `docs/STATIONS.md`, `data/out/layout.json` and M's `data/out/history/failure_modes.csv`.

### Integration monitor (http://localhost:8300)
Polls the engine every 2 s, draws OEE / throughput / M05 vibration + RUL / downtime cost with event markers, lists what changed (alerts, machine states, stopped stations, work orders), shows the brain's answer to each new alert or fault (auto-asked, with latency, tools, highlight, citations), has Inject fault / Clear faults / Ask buttons and a baseline-vs-now impact table.

## Evaluation
`brain/eval/questions.jsonl`: 40 questions with gold answers drawn from the data (who to page, fault codes, SOPs, parts, repeat failures, keep-running, live storylines, hero path). `run_eval.py` reports retrieval hit@6/MRR (free) and end-to-end pass rate. `run_ragas.py` adds RAGAS metrics (faithfulness, answer relevancy, context precision/recall) with a local Ollama judge in an isolated venv. `embed_experiment.py` compares local embedding models (dense / BM25 / hybrid). Latest numbers: `brain/eval/results_latest.json`, `brain/eval/ragas_latest.json`.
