# RCA-059: KSS-27008: Brake test failed on axis

**Machine:** BIW-WK-04 (Spot Weld Robot (KUKA) 4, KUKA KR 210 R2700 prime) - Area: Body-in-White
**Date:** 2026-09-25  **Shift:** A  **Downtime:** 412 min  **Estimated lost vehicles:** 172.6
**Work order:** WO-2026-007568  **Escalation level reached:** L6

## Problem statement
Operator reports: brake test failed on axis. Machine halted in cycle, alarm KSS-27008.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor KUKA was engaged.

## Investigation
Arrived 12:42. Repeated brake test. Measured motor_current_a = 23.83 A (nominal 18.0, warn 26.0, alarm 32.0). Cause: brake wear (excess braking angle).

## Root cause
Brake wear (excess braking angle) (category: Wear / aging).

## Corrective actions taken
Measured brake release voltage at the motor connector; Replaced motor with brake if wear exceeds limit; remaster.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Harold Thompson  Due: 2026-10-24
