# RCA-046: GP-SHOT-SLOW: Shot speed profile deviation / fill time out of window (~120 ms target)

**Machine:** M01 (Casting press, IDRA GIGAPRESS NEO 6100) - Area: Giga Casting & Machining
**Date:** 2026-05-22  **Shift:** A  **Downtime:** 307 min  **Estimated lost vehicles:** 167.2
**Work order:** WO-2026-003962  **Escalation level reached:** L6

## Problem statement
Casting press faulted (GP-SHOT-SLOW). Line lead called maintenance via radio at 09:41.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor IDRA was engaged.

## Investigation
On site 09:50. Followed troubleshooting steps in the IDRA GIGAPRESS NEO 6100 manual for GP-SHOT-SLOW. Measured hyd_pressure_bar = 255.68 bar (nominal 280, warn 255, alarm 235). Found: accumulator pre-charge low.

## Root cause
Accumulator pre-charge low (category: Unknown / under investigation).

## Corrective actions taken
1) Checked accumulator pre-charge. 2) Inspected shot sleeve and plunger tip.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Scott Hicks  Due: 2026-06-27
