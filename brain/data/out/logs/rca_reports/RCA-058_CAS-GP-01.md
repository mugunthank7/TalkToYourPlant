# RCA-058: GP-SHOT-SLOW: Shot speed profile deviation / fill time out of window (~120 ms target)

**Machine:** CAS-GP-01 (Giga Press 1, IDRA GIGAPRESS NEO 6100) - Area: Giga Casting & Machining
**Date:** 2026-09-25  **Shift:** A  **Downtime:** 387 min  **Estimated lost vehicles:** 190.6
**Work order:** WO-2026-007566  **Escalation level reached:** L6

## Problem statement
Intermittent GP-SHOT-SLOW over last hour, now hard-stopped. Operator noted reject rate creeping up.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor IDRA was engaged.

## Investigation
Initial check 08:20, Giga Press 1 fault GP-SHOT-SLOW confirmed. Measured hyd_pressure_bar = 254.83 bar (nominal 280, warn 255, alarm 235). Probable cause accumulator pre-charge low.

## Root cause
Accumulator pre-charge low (category: Unknown / under investigation).

## Corrective actions taken
Checked accumulator pre-charge.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Esperanza Kaur  Due: 2026-10-17
