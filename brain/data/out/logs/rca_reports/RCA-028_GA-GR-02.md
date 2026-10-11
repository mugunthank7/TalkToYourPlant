# RCA-028: KSS-27008: Brake test failed on axis

**Machine:** GA-GR-02 (Glazing Robot 2, KUKA KR 150 R3100 glazing) - Area: General Assembly
**Date:** 2025-11-20  **Shift:** B  **Downtime:** 321 min  **Estimated lost vehicles:** 93.2
**Work order:** WO-2025-008583  **Escalation level reached:** L5

## Problem statement
Intermittent KSS-27008 over last hour, now hard-stopped. Operator noted warm housing.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor KUKA was engaged.

## Investigation
Initial check 17:05, Glazing Robot 2 fault KSS-27008 confirmed. Measured motor_current_a = 25.78 A (nominal 18.0, warn 26.0, alarm 32.0). Probable cause brake contamination with lubricant.

## Root cause
Brake contamination with lubricant (category: Lubrication).

## Corrective actions taken
Repeated brake test. Measured brake release voltage at the motor connector. Replaced motor with brake if wear exceeds limit; remaster.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (current) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Arthur Bailey  Due: 2025-12-10
