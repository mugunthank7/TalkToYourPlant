# RCA-030: OVN-FAN-VIB: Recirculation fan high vibration

**Machine:** PNT-ASU-01 (Air Supply Unit 1, Duerr EcoSupply) - Area: Paint Shop
**Date:** 2026-01-19  **Shift:** A  **Downtime:** 307 min  **Estimated lost vehicles:** 91.8
**Work order:** WO-2026-000513  **Escalation level reached:** L5

## Problem statement
OVN-FAN-VIB displayed on HMI; Air Supply Unit 1 stopped after restart from break. Andon pulled at 10:26.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor Duerr was engaged.

## Investigation
Initial check 10:40, Air Supply Unit 1 fault OVN-FAN-VIB confirmed. Measured vibration_mm_s = 5.03 mm/s (nominal 2.2, warn 5.0, alarm 8.0). Probable cause bearing wear.

## Root cause
Bearing wear (category: Wear / aging).

## Corrective actions taken
Vibration analysis done: measurement; clean impeller.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (temperature) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Mei Ruiz  Due: 2026-02-02
