# RCA-033: OVN-FAN-VIB: Recirculation fan high vibration

**Machine:** PNT-ASU-02 (Air Supply Unit 2, Duerr EcoSupply) - Area: Paint Shop
**Date:** 2026-01-26  **Shift:** B  **Downtime:** 323 min  **Estimated lost vehicles:** 97.0
**Work order:** WO-2026-000719  **Escalation level reached:** L5

## Problem statement
OVN-FAN-VIB displayed on HMI; Air Supply Unit 2 stopped during start-up. Andon pulled at 15:43.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor Duerr was engaged.

## Investigation
On site 15:58. Followed troubleshooting steps in the Duerr EcoSupply manual for OVN-FAN-VIB. Measured vibration_mm_s = 5.51 mm/s (nominal 2.2, warn 5.0, alarm 8.0). Found: bearing wear.

## Root cause
Bearing wear (category: Wear / aging).

## Corrective actions taken
1) Vibration analysis done: measurement; clean impeller.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Raymond Nelson  Due: 2026-03-03
