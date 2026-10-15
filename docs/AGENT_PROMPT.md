# Prompt for another coding agent

Paste everything below the line into the other system.

---

You are joining an existing project. Work in a fresh clone and follow the plan; do not rewrite things that already work.

## Setup
1. Clone the repo: `git clone https://github.com/mugunthank7/TalkToYourPlant.git && cd TalkToYourPlant`
2. Read these first, in order: `CLAUDE.md`, `DECISIONS.md` (append-only decision log), `docs/V2_PLAN.md` (your plan), `docs/ANOMALY.md`, `docs/STATIONS.md`, `sim/README.md`, `brain/docs/BRAIN.md`.
3. Run what exists before changing it:
   - Engine: `cd sim && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m pytest tests -q` (about 12 tests, takes a minute or two).
   - Data generator: `cd data && pip install -r requirements.txt && python -m plantdata --seed 42 --out out`.
   - Brain: `pip install -r brain/requirements.txt`; tests `python3 brain/tests/test_graph.py` and `python3 brain/tests/test_index.py`.
   - Twin: `cd twin && npm install && npm run dev` (port 5180).

## What the project is
"Talk to Your Plant": a fictional EV factory ("Voltline EV Works") with a SimPy engine (`sim/plantsim`), an Isolation Forest + Shapley anomaly detector (`sim/plantsim/anomaly`), a React/three.js live twin and dashboard (`twin/`), and a rule-based chat "brain" with hybrid retrieval (`brain/`). Current weakness: the detector is evaluated only on faults our own generator made, there is one failure story (weld robot M05 bearing wear), and retrieval/agent quality is measured on a small question set.

## Your job
Execute `docs/V2_PLAN.md`, in the order it gives (Phase 0, 1, 4 evaluation harness, 3, 2, 5, 6). Start with Phase 0 and Phase 1. Candidate datasets (check each licence yourself and record it in `docs/DATASETS.md` before using it):
- NASA IMS bearings: https://data.nasa.gov/dataset/ims-bearings
- XJTU-SY and FEMTO-PRONOSTIA bearing run-to-failure sets (find and verify the original sources): index at https://github.com/VictorBauler/awesome-bearing-dataset
- FactoryNet robot bundle (CC BY 4.0): https://huggingface.co/datasets/Forgis/factorynet-hackathon
- Maintenance text: MWO2KG failure-mode set, MaintNorm, MaintNet (https://aclanthology.org/2020.coling-demos.2)
- Fleet data: SCANIA Component X (https://snd.se/en/catalogue/dataset/2024-34)
- OEE ranges for calibration: TeepTrak OEE Benchmark (https://teeptrak.com/en/?p=92585)

## Rules (important)
- **Ask before downloading anything**, one dataset at a time: state name, source, licence and size, then wait for a yes. Never commit raw data (git-ignore `data/real/`); commit fetch scripts and checksums.
- **Measure before you trust**: for every change, report before/after numbers on a held-out split (split by run or by question, never by window). Keep a baseline results file in `docs/results/`.
- Be honest in docs: synthetic vs real, what failed, what the numbers do not show.
- Keep the plant fictional; keep machine/station IDs (M01..M11, S01..S12) and graph node names stable (they are a contract).
- Add an entry to `DECISIONS.md` for each non-trivial choice (append, do not rewrite old entries).
- Seeds everywhere; scripts must be re-runnable; add tests for anything the engine or brain relies on.
- Small commits with imperative messages. **No co-author trailers. Do not push**; give me the push command at the end.
- Do not kill processes you did not start. The engine uses :8000, the brain :8100, the twin :5180; use other ports (for example 8010) for your own test servers.
- Do not make unrequested UI/visual changes. Do not turn on quality-reducing "low" render modes.

## First deliverable
Phase 0 + Phase 1: `docs/DATASETS.md`, fetch scripts, an IMS loader and feature pipeline, the detector trained on early-life windows only, and `docs/ANOMALY_REAL.md` with a results table (lead time before failure, false alerts, RUL error with intervals) against a fixed-threshold baseline. Report back with the numbers and the push command.
