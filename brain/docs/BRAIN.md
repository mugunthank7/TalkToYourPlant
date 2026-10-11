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

## Chat API
`POST /chat` `{message, session_id?, shift?}` returns:
```jsonc
{
  "answer": "text with inline [DOC-ID] citations",
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
`brain/app/sim_adapter.py` `LiveSim` calls the engine in `sim/` through its `/tools` endpoints:
`get_machine_health` + `get_anomaly_report` (sensors, alert level, contributors, RUL), `run_what_if` (baseline vs scenario KPIs), `create_work_order`.
Start the engine (`sim/README.md`, port 8000), then `SIM_MODE=live python3 brain/app/api.py`. Machines the engine does not simulate (all except `M01..M10`) fall back to the mock storyline data.
Status: verified against a stub that returns the shapes read from `sim/plantsim/tools.py`; **not yet run against the real engine** (its saved anomaly model needs a newer numpy than this machine has, and there was no network to install it).
Mock mode (default) builds from `data/out/events.json` and `data/out/scenarios/summary.json`.

## Evaluation
`brain/eval/questions.jsonl`: 40 questions with gold answers drawn from the data (who to page, fault codes, SOPs, parts, repeat failures, keep-running, live storylines, hero path). `run_eval.py` reports retrieval hit@6/MRR (free) and end-to-end pass rate. `run_ragas.py` adds RAGAS metrics (faithfulness, answer relevancy, context precision/recall) with a local Ollama judge in an isolated venv. `embed_experiment.py` compares local embedding models (dense / BM25 / hybrid). Latest numbers: `brain/eval/results_latest.json`, `brain/eval/ragas_latest.json`.
