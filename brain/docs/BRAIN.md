# Brain (T side): knowledge graph, hybrid RAG, Gemini agent, chat API

Fictional EV plant digital twin. The brain answers plant questions from tool results only, and tells the 3D twin which machines to highlight.

## Architecture
```
question -> Brain.ask (brain/app/agent.py)
              local (default): intent router -> tools -> deterministic renderer (no LLM, ~instant); Ollama only for unmatched questions
              gemini: tool-calling loop, max 6 steps
              |-- graph_lookup / escalation_chain   -> PlantGraph  (NetworkX, 5.7k nodes)   brain/app/graph.py
              |-- search_docs                       -> DocIndex    (MiniLM + BM25, RRF)     brain/app/index.py
              |-- get_sensor_state / run_scenario / create_work_order -> SimAdapter         brain/app/sim_adapter.py
              |-- highlight                         -> machine ids + graph path for the twin
           -> {answer, highlight, citations, actions, meta}   served by FastAPI            brain/app/api.py
```
Data: `brain/data/out/` (built by `brain/data/build_keyed.py`; Voltara dataset re-keyed to the twin's `M01..M11` ids, D-022).

## Run
```
pip install -r brain/requirements.txt
cp brain/.env.example brain/.env        # then set GEMINI_API_KEY (file is gitignored)
python3 brain/scripts/check_key.py      # lists models, tests one call per role
python3 brain/data/build_keyed.py       # only if brain/data/out is missing
python3 brain/app/api.py                # http://localhost:8100  (chat UI at /, POST /chat, GET /health)
python3 brain/tests/test_graph.py && python3 brain/tests/test_index.py
python3 brain/eval/run_eval.py          # 40 questions; add --retrieval-only for the free retrieval metrics
```

## Environment (brain/.env)
| var | default | meaning |
|---|---|---|
| `LLM_BACKEND` | ollama | `ollama` (local, free; default) or `gemini` (hosted tool-calling loop, costs money/quota) |
| `OLLAMA_MODEL` / `OLLAMA_URL` / `OLLAMA_NUM_CTX` | qwen2.5:7b / http://localhost:11434 / 6144 | local model, only used for open-ended questions the router cannot template |
| `LOCAL_NARRATE` | 0 | `1` makes the local LLM phrase every answer from the tool results (slow, can hallucinate) |
| `GEMINI_API_KEY` | none | only needed for `LLM_BACKEND=gemini` and RAGAS |
| `MODEL_AGENT` / `MODEL_LITE` / `MODEL_FALLBACK` | gemini-3.5-flash-lite / gemini-3.1-flash-lite / gemini-3.1-flash-lite | agent, cheap steps, fallback (separate quota bucket) |
| `MODEL_PREMIUM` | gemini-3.8-flash | used when request has `premium: true` (20 RPD free tier) |
| `EMBED_BACKEND` | local | `local` (sentence-transformers MiniLM, no quota) or `gemini` |
| `RPM_*`, `RPD_*`, `TPM_*` | just under free tier | client-side limits per role (agent, lite, premium, embed) |
| `SIM_MODE` | mock | `mock` or `live`; `SIM_URL` default `http://localhost:8000` |
| `BRAIN_PORT` | 8100 | API port |

## Chat API
`POST /chat` `{message, session_id?, premium?, shift?}` returns:
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
  "meta": {"model","degraded","error","llm_calls","contexts","sources_consulted","tools","shift","sim_mode","latency_s","cached"}
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

## Rate limits and fallbacks
Per-role sliding-window RPM and TPM, persisted daily budget (`brain/.cache/usage.json`), exponential backoff with jitter on 429/5xx. Failure ladder: agent model, fallback model, deterministic no-LLM answer (flagged `degraded`). Answers are cached by question, shift and prompt version. A chat turn costs 2 to 4 requests.

## What M needs for SIM_MODE=live
Proposed endpoints (see `brain/docs/CONTRACT_PROPOSALS.md`): `GET /state`, `POST /scenario`, `POST /work_order`. Until then `SIM_MODE=mock` builds from `data/out/events.json` and `data/out/scenarios/summary.json`.

## Evaluation
`brain/eval/questions.jsonl`: 40 questions with gold answers drawn from the data (who to page, fault codes, SOPs, parts, repeat failures, keep-running, live storylines, hero path). `run_eval.py` reports retrieval hit@6/MRR (free) and end-to-end pass rate. `run_ragas.py` adds RAGAS metrics (faithfulness, answer relevancy, context precision/recall) in an isolated venv. Latest numbers: `brain/eval/results_latest.json`, `brain/eval/ragas_latest.json`.
