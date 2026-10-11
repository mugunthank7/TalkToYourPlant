# RCA-060: GP-SHOT-SLOW: Shot speed profile deviation / fill time out of window (~120 ms target)

**Machine:** CAS-GP-01 (Giga Press 1, IDRA GIGAPRESS NEO 6100) - Area: Giga Casting & Machining
**Date:** 2026-10-02  **Shift:** B  **Downtime:** 319 min  **Estimated lost vehicles:** 123.8
**Work order:** WO-2026-007763  **Escalation level reached:** L6

## Problem statement
Operator reports: shot speed profile deviation / fill time out of window (~120 ms target). Machine halted in cycle, alarm GP-SHOT-SLOW.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor IDRA was engaged.

## Investigation
On site 15:21. Followed troubleshooting steps in the IDRA GIGAPRESS NEO 6100 manual for GP-SHOT-SLOW. Measured hyd_pressure_bar = 256.76 bar (nominal 280, warn 255, alarm 235). Found: accumulator pre-charge low.

## Root cause
Accumulator pre-charge low (category: Unknown / under investigation).

## Corrective actions taken
1) Checked accumulator pre-charge.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Frank Patel  Due: 2026-10-21
