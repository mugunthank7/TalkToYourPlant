# Contract proposals (T to M)

The shared interface in `CLAUDE.md` is untouched. These are proposals; the brain works today against `SIM_MODE=mock`.

## 1. Engine HTTP endpoints the brain will call (D-016)
| call | body | returns |
|---|---|---|
| `GET /state` | none | `{"machines": {"M05": {"status":"ok|warning|critical", "readings": {...}, "alert": <alert msg or null>}}, "ts": ...}` |
| `POST /scenario` | `run_scenario` message from CLAUDE.md | `scenario_result` message (kpis: throughput_per_hr, downtime_min, oee, failure_probability, cost_usd) |
| `POST /work_order` | `{machine_id, component_id, spare_part, fault_code, priority, note}` | `work_order` message with `id` |
Questions for M: base URL and port; is `GET /state` per machine or full plant; does `scenario_result` include baseline vs scenario for each KPI (the mock does)?

## 2. Highlight message for the 3D window
The brain returns `highlight.machine_ids` (+ `graph_path` in the existing `graph_path` shape) with every chat answer. Proposal: the twin consumes this from `POST /chat` directly, or the brain relays a WebSocket message `{"type":"highlight","machine_ids":[...]}`. Pick one.

## 3. Alert payload
The mock `alert` uses the contract shape with illustrative SHAP values. When anomaly detection exists (owner open, D-019), please send real contributors; the brain only passes them through.

## 4. Scope note
Only M05 has a modelled fault in the engine outputs. The brain's knowledge base covers 119 machines and the live storylines (`CAS-GP-01`, `PNT-PR-04`, `BAT-BL-01`, `BIW-WK-03`, `UTL-CP-02`, `GA-TQ-07`); their sensor drift comes from the Voltara contract in mock mode.
