# Contract notes (T to M)

Superseded: the earlier endpoint proposals are replaced by M's real engine API (`sim/README.md`). The brain now uses `/tools/get_machine_health`, `/tools/get_anomaly_report`, `/tools/run_what_if` and `/tools/create_work_order`.

## Open items
1. **Highlight to the 3D twin.** The brain returns `highlight.machine_ids` and a `graph_path` (same shape as the twin's `graph_path` message) in every `POST /chat` answer (port 8100). The twin needs to call `/chat` or receive these over the engine WebSocket. Pick one.
2. **What-if scope.** The brain passes `keep_running {hours}` only. `failure_probability` is not in the engine's what-if output, so the brain shows it as not modelled.
3. **Machine coverage.** The engine models `M01..M10`. The knowledge base covers 119 machines and six live storylines (`CAS-GP-01`, `PNT-PR-04`, `BAT-BL-01`, `BIW-WK-03`, `UTL-CP-02`, `GA-TQ-07`); those answer from the mock storyline data until the engine models them.
4. **Real run.** Confirm one end-to-end `SIM_MODE=live` run against the real engine (shapes were read from source, not observed).
