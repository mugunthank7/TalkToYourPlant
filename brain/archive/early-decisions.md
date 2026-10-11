# Decisions & Change Log

Append-only record of every change and feature. Newest at bottom. Number entries sequentially.
Use it to find why something exists and to roll back or revisit.

## Entry template

```
### #N — <short title>
- **Date:** YYYY-MM-DD
- **Type:** feature | change | fix | refactor | dependency | structure | decision
- **Status:** active | superseded by #X | reverted
- **What:** what changed
- **Why:** reason, problem solved
- **Alternatives:** options considered, why rejected
- **Files:** paths touched
- **How to revert:** steps to undo, if non-trivial
```

## Index

| # | Date | Type | Title | Status |
|---|------|------|-------|--------|
| 1 | 2026-10-10 | structure | Create CLAUDE.md and DECISIONS.md | active |
| 2 | 2026-10-10 | decision | Define project vision, scope, and phase | active |
| 3 | 2026-10-10 | decision | Use GraphRAG (multimodal) for the brain | active |
| 4 | 2026-10-10 | decision | Demo domain = EV manufacturing, simulated data | active |
| 5 | 2026-10-10 | decision | Graph-anchored multimodal RAG pattern | proposed |
| 6 | 2026-10-10 | decision | Hybrid data: synthetic backbone + public datasets | proposed |
| 7 | 2026-10-10 | structure | Add domain brief PDF | active |

---

## Log

### #1 — Create CLAUDE.md and DECISIONS.md
- **Date:** 2026-10-10
- **Type:** structure
- **Status:** active
- **What:** Added `CLAUDE.md` (project context: goal, structure, framework, why) and `DECISIONS.md` (this change log).
- **Why:** Give Claude persistent project context each session, and keep a record of every change/feature so we can return to any of them later.
- **Alternatives:** Relying on git history only — no git repo yet, and commit messages lack reasoning.
- **Files:** `CLAUDE.md`, `DECISIONS.md`
- **How to revert:** Delete both files.

### #2 — Define project vision, scope, and phase
- **Date:** 2026-10-10
- **Type:** decision
- **Status:** active
- **What:** Project = "Talk to Your Plant", a digital twin of a plant (factory, oil rig, UPS/inventory store, village) users converse with. Components: brain (multimodal GraphRAG), digital twin, conversational interface, KPI dashboard, what-if simulator. Personas: employees, machinery keepers, inventory keepers, managers. Positioned as advanced ERP with live data.
- **Why:** One conversational place that knows all plant state; lets users test what-if before acting.
- **Alternatives:** None discussed.
- **Files:** `CLAUDE.md`
- **How to revert:** n/a (vision doc).

### #3 — Use GraphRAG (multimodal) for the brain
- **Date:** 2026-10-10
- **Type:** decision
- **Status:** active
- **What:** Brain = multimodal RAG built on a graph (GraphRAG), not plain vector RAG.
- **Why:** Entities (machines, tasks, people, inventory) are heavily interconnected; graph keeps them linked, better multi-hop answers, lower latency.
- **Alternatives:** Plain vector RAG — weaker on relationships. Not formally compared yet.
- **Files:** `CLAUDE.md`
- **How to revert:** n/a until code exists. Stack/graph DB choice still open.

### #4 — Demo domain = EV manufacturing, simulated data, brain-first
- **Date:** 2026-10-10
- **Type:** decision
- **Status:** active
- **What:** Model an EV vehicle manufacturing company as demo plant. All data simulated. Current phase builds only the brain; dashboard and simulator deferred.
- **Why:** Rich domain (machinery, workforce, inventory, wear, shifts) to prove the twin concept; brain is foundation everything else needs.
- **Alternatives:** Oil rig, UPS store — kept as future plant types, design should stay plant-agnostic.
- **Files:** `CLAUDE.md`
- **How to revert:** n/a.

### #5 — Graph-anchored multimodal RAG pattern
- **Date:** 2026-10-10
- **Type:** decision
- **Status:** proposed (awaiting user confirmation)
- **What:** Modalities: text, images, sensor time series. Every evidence item (chunk, image, sensor window) is a node linked to a plant entity. Retrieval = entity link, graph walk, fetch attached evidence. Raw time series stay in a time-series store; only windows/features/anomaly/RUL events enter the graph.
- **Why:** Questions are multi-hop and entity-centric (vehicle -> stage -> part -> supplier). Restricting vector search to entity-attached evidence keeps latency low.
- **Alternatives:** Text-ify everything (good baseline, loses image detail); shared multimodal embedding space (use for images only); per-modality stores + router (storage layer only). Whole-corpus GraphRAG community summaries: one benchmark found latency poor for real time (single source, not controlled).
- **Files:** `docs/talk-to-your-plant-domain-brief.pdf`
- **How to revert:** n/a, no code yet.

### #6 — Hybrid data strategy: synthetic backbone + public datasets
- **Date:** 2026-10-10
- **Type:** decision
- **Status:** proposed
- **What:** No public EV-plant dataset exists. Generate synthetic ERP backbone (workers, shifts, BOM, inventory, POs, vehicles, stages) and LLM-written SOPs/logs. Attach public data for signal realism: NASA C-MAPSS and AI4I 2020 (sensors/RUL), NASA Li-ion battery aging, CWRU/Paderborn bearings, MVTec AD and Severstal (images), DataCo (orders/lead times). Public sets are relabelled as stand-ins and disclosed as such in the demo.
- **Why:** Hackathon needs deployable, near-real-time, controllable data. Proprietary plant data unavailable.
- **Alternatives:** Only synthetic (less realistic signals); only public (no coherent plant story).
- **Files:** `docs/talk-to-your-plant-domain-brief.pdf`
- **How to revert:** n/a. Unchecked items: Bosch line data, SECOM, NHTSA, CWRU/Paderborn official links, MVTec license terms.

### #7 — Add domain brief PDF
- **Date:** 2026-10-10
- **Type:** structure
- **Status:** active
- **What:** Added `docs/talk-to-your-plant-domain-brief.pdf`: multimodal RAG options, ontology, retrieval flow, data sources, real-time layer, 6 showcase user stories, KPI handoff, build order.
- **Why:** Side reference while building; shared vocabulary with the teammate doing twin/KPI dashboard.
- **Alternatives:** Markdown only; user asked for PDF.
- **Files:** `docs/talk-to-your-plant-domain-brief.pdf`
- **How to revert:** Delete file.
