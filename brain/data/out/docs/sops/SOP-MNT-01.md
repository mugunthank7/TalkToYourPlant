# SOP-MNT-01: Fault Escalation and Paging Protocol

**Area:** ALL  |  **Owner:** Maintenance Manager  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Purpose
Ensure the right person is engaged at the right time when equipment faults, defining who to page, when, and how quickly they must acknowledge.

## Roles
- **Operator:** first responder. Pull the Andon, note time and fault code, tell the Line Lead.
- **Line Lead (L0):** confirms the stop, tries a safe reset (once), calls the on-shift Primary Technician for the machine (radio channel MAINT or pager).
- **L1 Primary Technician:** the on-shift technician assigned to the machine in the trade matching the fault (mechanical, electrical, hydraulics, robotics, controls, process).
- **L2 Backup Technician:** same trade, same shift; paged if no ack within 5 minutes or if a second person is required (two-person work).
- **L3 Maintenance Supervisor (shift):** for the zone; paged on thresholds below, any severity-3+ fault, or any safety concern.
- **L4 Area Engineer (on-call):** reliability, controls or process engineer for the area, selected by fault trade.
- **L5 Vendor support:** OEM emergency line per machine (see machine record for contract and SLA).
- **L6 Plant management:** Maintenance Manager, Operations Director, Plant Manager; always engaged immediately for safety events.

## Escalation timers (minutes of line-impacting downtime)
| Machine criticality | L1 tech | L2 backup | L3 supervisor | L4 engineer | L5 vendor | L6 plant mgmt |
|---|---|---|---|---|---|---|
| A (line-stopping) | 2 | 8 | 15 | 30 | 90 | 180 |
| B (buffered) | 5 | 15 | 30 | 60 | 180 | 360 |
| C (non-critical) | 10 | 30 | 60 | 120 | 360 | 720 |

Timers run from the Andon. A repeat of the same fault within 24 hours moves the escalation straight to L4.

## Acknowledgement
Pages must be acknowledged within 3 minutes (A), 5 minutes (B), 10 minutes (C). If no ack, the sender pages the next level and calls the radio/phone. The Maintenance Supervisor can reassign technicians across trades.

## Fault-trade routing
- Robot alarm (SRVO-/KSS-/ABB-): ROBO tech; controls engineer for DCS/safety parameter issues.
- Hydraulic pressure/temperature/leak: HYD tech.
- Drive overload, breakers, motors: ELEC tech.
- PLC/MES comms, AGV navigation: CTRL tech.
- Torque NOK, calibration, process drift, laser power: PROC tech with process engineer.
- Mechanical wear/jam: MECH tech.

## Safety overrides
Injury, fire/smoke, HV event, paint Ex-purge fault, molten metal or die water leak: **Level 6 immediately**, follow SOP-SAF-03 / SOP-CAS-02 / SOP-PNT-01.

## Communication
Use the area channel for status every 15 minutes during Level 3+ events. The Maintenance Supervisor posts the event summary into the shift handover (SOP-MNT-03). After vendor engagement the Planner opens a service ticket in CMMS.

## Who to page when information is incomplete
Page the **Maintenance Supervisor** for the zone; they know the on-call rota. The on-call rota (weekly) lists primary and secondary engineers per discipline.

## References
- Internal
