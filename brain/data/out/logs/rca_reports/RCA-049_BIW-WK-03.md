# RCA-049: KSS-GEAR-LEAK: Oil leak detected at A1-A3 gearbox seal

**Machine:** BIW-WK-03 (Spot Weld Robot (KUKA) 3, KUKA KR 210 R2700 prime) - Area: Body-in-White
**Date:** 2026-07-10  **Shift:** A  **Downtime:** 301 min  **Estimated lost vehicles:** 107.8
**Work order:** WO-2026-005380  **Escalation level reached:** L6

## Problem statement
Operator reports: oil leak detected at A1-A3 gearbox seal. Machine halted in cycle, alarm KSS-GEAR-LEAK.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor KUKA was engaged.

## Investigation
On site 07:23. Followed troubleshooting steps in the KUKA KR 210 R2700 prime manual for KSS-GEAR-LEAK. Measured gearbox_temp_c = 67.55 C (nominal 48.0, warn 70.0, alarm 82.0). Found: over-filled gearbox.

## Root cause
Over-filled gearbox (category: Unknown / under investigation).

## Corrective actions taken
1) Inspected and photograph leak source.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Lena Lopez  Due: 2026-07-24
