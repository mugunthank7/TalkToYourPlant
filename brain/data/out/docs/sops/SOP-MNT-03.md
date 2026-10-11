# SOP-MNT-03: Shift Handover Protocol

**Area:** ALL  |  **Owner:** Production Supervisor  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Purpose
Preserve continuity of equipment status, open issues and safety information between shifts A (06:00-14:00), B (14:00-22:00) and C (22:00-06:00).

## Overlap and format
15-minute overlap at the area board. Outgoing supervisor and maintenance supervisor brief the incoming pair using the handover sheet.

## Handover content
1. Safety events and near misses.
2. Output vs plan, scrap and quality holds.
3. Downtime events with work order numbers, status (repaired/temporary fix/waiting parts).
4. Machines under watch (trending sensors, recently repaired).
5. Equipment under LOTO or in bypass (list each lock and owner).
6. PMs and inspections planned for the next shift.
7. Vendor activity and open service tickets.

## Rules
- A temporary fix must state exit criteria and a time limit.
- No machine in bypass may be handed over without supervisor approval.
- The notes are saved in the CMMS shift log and are searchable for the next 12 months.

## References
- Internal
