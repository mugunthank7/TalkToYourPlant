# RCA-016: CNV-CHAIN-STRETCH: Chain elongation beyond limit

**Machine:** LOG-CR-01 (Overhead Crane 1, Konecranes CXT 20 t) - Area: Intralogistics
**Date:** 2025-04-17  **Shift:** A  **Downtime:** 389 min  **Estimated lost vehicles:** 68.0
**Work order:** WO-2025-002648  **Escalation level reached:** L6

## Problem statement
CNV-CHAIN-STRETCH displayed on HMI; Overhead Crane 1 stopped after restart from break. Andon pulled at 09:26.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor Konecranes was engaged.

## Investigation
Arrived 09:36. Measured elongation (>3% replace). Measured vibration_mm_s = 4.81 mm/s (nominal 1.5, warn 4.5, alarm 7.0). Cause: wear / lack of lubrication.

## Root cause
Wear / lack of lubrication (category: Lubrication).

## Corrective actions taken
Measured elongation (>3% replace).

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (current) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Kyle Phillips  Due: 2025-05-19
