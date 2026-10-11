# RCA-015: KSS-27008: Brake test failed on axis

**Machine:** BIW-WK-07 (Spot Weld Robot (KUKA) 7, KUKA KR 210 R2700 prime) - Area: Body-in-White
**Date:** 2025-03-31  **Shift:** A  **Downtime:** 328 min  **Estimated lost vehicles:** 201.5
**Work order:** WO-2025-002220  **Escalation level reached:** L6

## Problem statement
KSS-27008 displayed on HMI; Spot Weld Robot (KUKA) 7 stopped after a die/tool change. Andon pulled at 13:36.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor KUKA was engaged.

## Investigation
Arrived 13:47. Repeated brake test. Measured motor_current_a = 24.46 A (nominal 18.0, warn 26.0, alarm 32.0). Cause: brake wear (excess braking angle).

## Root cause
Brake wear (excess braking angle) (category: Wear / aging).

## Corrective actions taken
Measured brake release voltage at the motor connector.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Kenneth Silva  Due: 2025-05-06
