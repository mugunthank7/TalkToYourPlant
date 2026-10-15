# Plan for v2: from a convincing demo to something measured on real data

Goal: keep the synthetic plant for the twin, but stop grading ourselves on data we generated. Every claim in v2 should be backed by a number from data we did not make, with the limits stated.

## Phase 0, foundations (1 day)
- `docs/DATASETS.md`: one row per dataset (source URL, licence, size, what it is used for, how to fetch it). Licence is checked and written down before anything is downloaded.
- `data/real/` (git-ignored) plus `scripts/fetch_*.py` that download, verify a checksum and unpack. No raw data in git.
- Shared evaluation conventions: seeds, splits by *run* (never by window), one results JSON per experiment under `docs/results/`.

## Phase 1, detector on real bearings (3 to 4 days)  **do first**
- Datasets: NASA IMS (run-to-failure, 20 kHz), then XJTU-SY and/or FEMTO-PRONOSTIA for generalisation.
- Work: loaders; features at the engine's 1-minute level (RMS, kurtosis, band energy around the bearing defect frequencies, load-normalised where load exists); train the Isolation Forest on early-life windows only; evaluate lead time before failure, false alerts, and RUL error with conformal intervals, split by bearing run.
- Baselines to beat and report: a fixed RMS threshold and a "2x baseline" rule.
- Output: `docs/ANOMALY_REAL.md` with a table next to the synthetic results, including where it fails.
- Then fit the degradation growth curves from the real runs and use them as the engine's wear prior (replaces our invented exponential).

## Phase 2, robot and weld signals (3 days)
- Datasets: FactoryNet bundle (CC BY 4.0), voraus-AD, AURSAD, METALLICADOUR; optionally Intel welding or the spot-welding IEEE DataPort set (check licences).
- Work: a joint-current/torque anomaly model for the weld robots; fault-type classification with SHAP; report per-dataset results.

## Phase 3, more than one failure story in the engine (3 days)
- `POST /fault` takes a `mode` (bearing wear, servo/current drift, lubrication loss, clamp leak, ...); each mode has its own sensor signature from Phases 1 and 2.
- Generalise the hero logic so any machine can degrade; the detector explains which mode; the brain catalogue maps modes to SOPs and parts.
- The 30-day history gets incidents on several machines.

## Phase 4, retrieval and agent quality (4 to 5 days)
- Evaluation first: grow the question set to 300+ with paraphrases and messy wording; metrics hit@k, MRR, nDCG, plus answer checks (cited documents apply to the machine, numbers appear in tool results). A baseline file and a one-command report.
- Held-out text: MWO2KG (failure-mode labelled work orders), MaintNorm; use as extra test data for retrieval and classification.
- Then measure each change against the baseline: cross-encoder re-ranker, query rewriting (ids to names, typos, intent hints).
- Make the router an explicit state machine (classify, plan tools, run, check evidence, answer or ask a clarifying question), LangGraph or plain Python, with the path recorded per answer.
- Evidence panel in the chat UI: documents used, engine values, confidence.

## Phase 5, make it easy to run and show (2 days)
- One start/stop command, a "reset to the hero moment" button, health checks for all services, a recorded demo video, a hosted read-only demo if possible.

## Phase 6, write-up (1 day)
- Results page with tables, honest limits, and what would change on a real plant.

## Order and why
Phase 0, 1, 4 (evaluation harness), 3, 2, 5, 6. Phase 1 is the biggest credibility gain. The Phase 4 harness comes early so later retrieval changes are judged by numbers.

## Rules that carry over
- Fictional plant, no real brands; IDs and node names are a contract (see CLAUDE.md and `docs/STATIONS.md`).
- Add a DECISIONS.md entry for every non-trivial choice.
- Small commits, no co-author trailers, no pushing (the owner pushes).
- Downloads are approved one dataset at a time; licences recorded first.
