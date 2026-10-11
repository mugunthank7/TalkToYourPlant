# Talk to Your Plant

> Project context for Claude. Read this first every session. Keep it current.

## Goal
Build a **digital twin of a "plant"** that people can talk to. "Plant" = any self-contained operation: factory, oil rig facility, UPS store / inventory warehouse, small village. Twin is a digital clone of the whole operation: people, machines, inventory, tasks, live data.

**Demo domain:** EV (electric vehicle) manufacturing company.

Think: advanced ERP, but with **live data**, a conversational interface, KPI dashboard, and what-if simulation.

## Current phase
**Brain only.** Focus now = build the knowledge/reasoning layer (multimodal GraphRAG). UI, dashboard, simulator come after. Everything is simulated data for now, no real plant connection.

## Why
- One place that knows everything about the plant: what tasks run, who does them, which machines, what stock.
- Managers and workers ask in natural language instead of digging through ERP screens.
- Live data + simulation lets users test "what if" before acting in the real world.
- GraphRAG: facts well connected (machine ↔ task ↔ person ↔ inventory), lower latency, better multi-hop answers than plain vector RAG.

## Core components
1. **Brain (current focus):** multimodal GraphRAG knowledge base for the plant.
2. **Digital twin:** live model of company, tasks, machines, people, inventory.
3. **Conversational interface:** users talk to the twin.
4. **KPI dashboard:** (later)
5. **What-if scenario simulator:** (later)

## Brain knowledge scope (EV manufacturing)
- Company info, org structure, roles and what they are called
- Machinery: types, count, specs, wear / health, maintenance
- Workforce: headcount, roles, shifts, ideal working hours
- Vehicles: wear, production state
- Inventory: parts, stock levels, suppliers
- Tasks / processes: what is happening on the floor, live
- Multimodal: text, docs, tables, images, sensor/time-series (exact modalities TBD)

## Users and personas
Each persona gets own stories and views of the twin:
- **Employees / workers:** their tasks, shifts, hours
- **Machinery keepers (maintenance):** machine health, wear, downtime
- **Inventory keepers:** stock, reorder, supply
- **Managers:** whole-plant view, KPIs, what-if decisions

(Persona stories to be written, track in `DECISIONS.md`.)

## Framework / Stack
Proposed (see DECISIONS #5, #6, not yet confirmed): graph-anchored multimodal RAG; Neo4j (graph + vector index); TimescaleDB or DuckDB for sensors; Python; simulator emitting events on a stream. Still open: embedding/multimodal model, LLM, orchestration, final graph DB, live data transport. Each choice gets logged in `DECISIONS.md`.

## Structure
```
talkToYourPlant/
├── CLAUDE.md       # project context (this file)
├── DECISIONS.md    # change log + decision record
└── docs/
    └── talk-to-your-plant-domain-brief.pdf  # domain reference: RAG options, ontology, data sources, user stories
```
Update as code folders are added.

## Conventions
TBD.

## How to run / test
TBD.

## Working rules
- **Log every change and discussion outcome in `DECISIONS.md`.** New feature, refactor, dependency, structure change, design discussion, or reversal = new entry, same turn as the change.
- Before changing existing feature, check `DECISIONS.md` for why it exists.
- Update this file when goal, stack, or structure change.
- Never delete old decision entries. If reversed, add new entry and mark old one `Superseded by #N`.
