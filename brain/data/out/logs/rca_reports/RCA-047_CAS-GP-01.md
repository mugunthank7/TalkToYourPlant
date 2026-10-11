# RCA-047: GP-SHOT-SLOW: Shot speed profile deviation / fill time out of window (~120 ms target)

**Machine:** CAS-GP-01 (Giga Press 1, IDRA GIGAPRESS NEO 6100) - Area: Giga Casting & Machining
**Date:** 2026-05-22  **Shift:** B  **Downtime:** 298 min  **Estimated lost vehicles:** 114.4
**Work order:** WO-2026-003966  **Escalation level reached:** L6

## Problem statement
At 17:34 Giga Press 1 went down with GP-SHOT-SLOW. Operator tried reset twice, alarm returned.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor IDRA was engaged.

## Investigation
On site 17:46. Followed troubleshooting steps in the IDRA GIGAPRESS NEO 6100 manual for GP-SHOT-SLOW. Measured hyd_pressure_bar = 256.61 bar (nominal 280, warn 255, alarm 235). Found: accumulator pre-charge low.

## Root cause
Accumulator pre-charge low (category: Unknown / under investigation).

## Corrective actions taken
1) Checked accumulator pre-charge. 2) Inspected shot sleeve and plunger tip. 3) Calibrated injection valve.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (temperature) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Henry Joshi  Due: 2026-06-20
