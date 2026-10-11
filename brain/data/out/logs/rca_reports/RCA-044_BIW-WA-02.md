# RCA-044: ABB-38103: Brake failure on axis

**Machine:** BIW-WA-02 (Handling/Weld Robot (ABB) 2, ABB IRB 6700-235/2.65) - Area: Body-in-White
**Date:** 2026-05-13  **Shift:** B  **Downtime:** 344 min  **Estimated lost vehicles:** 113.6
**Work order:** WO-2026-003706  **Escalation level reached:** L6

## Problem statement
Intermittent ABB-38103 over last hour, now hard-stopped. Operator noted nothing unusual before the stop.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor ABB was engaged.

## Investigation
On site 16:39. Followed troubleshooting steps in the ABB IRB 6700-235/2.65 manual for ABB-38103. Measured motor_current_a = 27.52 A (nominal 18.0, warn 26.0, alarm 32.0). Found: brake wear.

## Root cause
Brake wear (category: Wear / aging).

## Corrective actions taken
1) Ran brake check.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Samantha Stewart  Due: 2026-06-11
