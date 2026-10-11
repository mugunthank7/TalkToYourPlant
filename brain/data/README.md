# brain/data

T-side (knowledge base) dataset, keyed to the twin's IDs.

- `voltara_gen/`: synthetic plant generator (stdlib only, seeded). Produces 119 machines, 452 employees, ~20k work orders, 83 SOPs/manuals, ~11k RAG chunks, graph seed. See its README and SOURCES.md.
- `crosswalk_*.csv`: twin IDs (`M01..M11`, `S01..S12`, `A-TECH01`...) mapped to Voltara IDs and signals. **Twin IDs win** (D-021/D-022).
- `build_keyed.py`: runs the generator, re-keys mapped entities to twin IDs, adds gap machines (`M03`, `M10`) and the hero `M05` bearing-wear content, runs integrity checks.
- `hero_m05_messages.json`: example `alert` and `graph_path` messages for M05, matching the interface contract in `../../CLAUDE.md`.
- `out/`: generated, gitignored (about 46 MB). Rebuild with `python3 build_keyed.py` (about 3 s).

## Layout of `out/`
```
master/   machines.csv (+voltara_id, twin_station), employees, escalation_matrix.json, spare_parts.csv, ...
logs/     work_orders, incidents, service logs, handover notes, rca_reports
docs/     sops/ (incl. SOP-MNT-M05-01), manuals/
rag/      rag_chunks.jsonl, graph_nodes.jsonl, graph_edges.jsonl
contracts/ simulator_interface.json, hero_m05_messages.json
```

## What is real vs synthetic
Everything is synthetic. Some OEM fault-code facts are tagged `oem_public` (see `voltara_gen/SOURCES.md`). The hero bearing-wear fault, SOP-MNT-M05-01, `bearing_6208`, and the M03/M10 stubs are authored for this demo and tagged `synthetic`.

## Mapping notes
- M05 maps to KUKA `BIW-WK-05`. Voltara's own storyline on `BIW-WK-03` (gearbox oil leak) is untouched and available as a contrast case.
- Four twin employees (`A-TECH01`, `B-TECH01`, `A-SUP01`, `B-SUP01`) replace the matching Voltara people in M05's escalation chain, so the technician who walks in the 3D scene is the one the chatbot says to page.
- The other ~108 Voltara machines are knowledge-base only (not rendered in 3D).
