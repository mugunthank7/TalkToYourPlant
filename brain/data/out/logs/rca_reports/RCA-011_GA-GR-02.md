# RCA-011: KSS-27008: Brake test failed on axis

**Machine:** GA-GR-02 (Glazing Robot 2, KUKA KR 150 R3100 glazing) - Area: General Assembly
**Date:** 2025-02-12  **Shift:** C  **Downtime:** 405 min  **Estimated lost vehicles:** 77.9
**Work order:** WO-2025-001056  **Escalation level reached:** L6

## Problem statement
Intermittent KSS-27008 over last hour, now hard-stopped. Operator noted reject rate creeping up.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor KUKA was engaged.

## Investigation
On site 02:52. Followed troubleshooting steps in the KUKA KR 150 R3100 glazing manual for KSS-27008. Measured motor_current_a = 26.47 A (nominal 18.0, warn 26.0, alarm 32.0). Found: brake wear (excess braking angle).

## Root cause
Brake wear (excess braking angle) (category: Wear / aging).

## Corrective actions taken
1) Repeated brake test. 2) Measured brake release voltage at the motor connector.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Bianca Singh  Due: 2025-02-27
