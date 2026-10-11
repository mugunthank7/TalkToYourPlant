# Handoff: what the brain side changed, and where to pick up

Read this first. Everything below is on `main` after PR #3. Decisions D-033 to D-052 in `DECISIONS.md` have the reasoning.

## 1. Files changed OUTSIDE `brain/` (your territory, please review)
| File | Change | Why |
|---|---|---|
| `twin/src/state.ts` | + `selectedStation`, `setSelectedStation` | Click-a-station |
| `twin/src/scene/Plant.tsx` | station group `onClick`, invisible hit box, cyan outline, pointer cursor | Click-a-station |
| `twin/src/ui/Hud.tsx` | placeholder chat button replaced with a working chat; `<StationPanel />` mounted | Brain chat |
| `twin/src/styles.css` | styles for the station panel, report card, chat | UI |
| `twin/src/brain.ts` (new) | `BRAIN` url (`VITE_BRAIN_URL`, default `http://localhost:8100`), `brainGet`, `brainPost` | Brain link |
| `twin/src/ui/StationPanel.tsx` (new) | the panel; renders the structured `report` | Click-a-station |
| `DECISIONS.md` | D-033 to D-052 appended | Log |
| `CLAUDE.md` | "Brain (T side)" section | Docs |
Nothing in `sim/`, `data/`, `assets/` was modified.

## 2. What the brain provides (all under `brain/`)
- **Knowledge**: graph (NetworkX, 5.7k nodes), 11k RAG chunks (SOPs, manuals, work orders, RCAs, stations, failure catalogue), keyed to your `M01..M11` / `S01..S12` ids.
- **Answers**: `POST /chat` and `GET /station/{id}` on :8100. Every answer is a structured card (`report`: severity, headline, what_happened, impact, do_now, contacts, parts, procedure, sources) plus `confidence`.
- **Engine link**: `brain/app/sim_adapter.py` reads one cached `/state` snapshot and calls `/tools/run_what_if` and `/tools/create_work_order`; `/fault` for failure injection.
- **No hosted LLM, no key**: deterministic intent router; local Ollama only for the optional "LLM plan".
- **Tooling**: monitor :8300, run dashboard :8200, eval (40 questions), demo set (18 questions), embedding experiment, RAGAS.

## 3. Run it
```bash
brain/scripts/start_all.sh          # engine :8000, brain :8100, dashboard :8200, monitor :8300, twin :5180
python3 brain/eval/demo_check.py --reset      # 18 demo questions, expects 18/18 high confidence
python3 brain/tests/test_graph.py && python3 brain/tests/test_index.py
python3 brain/eval/run_eval.py                # 40 questions, expects 40/40
brain/scripts/stop_all.sh
```
Engine venv: `python3 -m venv sim/.venv`, then install `sim/requirements.txt` package by package (a bulk install failed with DNS errors on this network). The saved anomaly model needs numpy 2 / scikit-learn 1.9, so the engine runs from `sim/.venv`, not the brain's environment.
Rebuild brain data after changing `docs/STATIONS.md`, `data/out/layout.json` or the failure catalogue: `python3 brain/data/build_keyed.py` (about 3 s, deterministic).

## 4. How to extend the brain
- **New question type**: add a branch in `Brain._route` (regex + tools to run), then a block in `Brain._report` that turns the tool results into the card fields. Add a question to `brain/eval/questions.jsonl` (via `make_questions.py`) and, if demo-worthy, to `brain/eval/demo_questions.json`.
- **New machine or station facts**: update `docs/STATIONS.md` / `layout.json`, rebuild with `build_keyed.py`.
- **Wording of unknown questions**: `Brain._fallback` (glossary, no-such-area, purchase requests, off-topic). Keep it plain; no "as an AI".
- Never cache answers in live mode (engine state changes); the code already skips the cache.

## 5. Open work, in priority order
1. **3D highlight from the brain**: chat answers return `highlight.machine_ids` and `graph_path`; the twin only selects the station of the first machine. Animate the graph path over the scene (your `graph_path` message shape matches).
2. **Failure-mode-specific injection**: the engine injects faults per machine (`POST /fault`), not per failure mode, so the panel lists modes but "Simulate failure here" breaks the machine generically. Add `mode` to `/fault` and the sensor signature, and the brain can show a different story per mode.
3. **Panel in the twin dashboard tab** and a station-level history (last N events per station).
4. **PM schedule lookup**: "When is the next maintenance for the press?" has no data source yet.
5. **Voice and photo input** (original whiteboard): not built. `qwen2.5vl:3b` is installed locally for the photo part.
6. **Real SHAP in older answers**: mock mode still uses illustrative contributors; live mode uses yours.
7. Install `twin` deps if missing: `cd twin && npm install` (this repo's `node_modules` is not committed).

## 6. Known issues
- First request after a restart takes about 8 s (index load).
- "Ask the local LLM for a plan" takes 30 to 70 s on an 8 GB machine and can strain memory; the deterministic card is the primary answer.
- The old Gemini API key was pasted into a chat once; it is not in the repo or its history, but should be deleted at aistudio.google.com/app/apikey.
- RAGAS scores come from a 3.8B local judge: indicative only.
