# RCA-038: GP-SHOT-SLOW: Shot speed profile deviation / fill time out of window (~120 ms target)

**Machine:** CAS-GP-01 (Giga Press 1, IDRA GIGAPRESS NEO 6100) - Area: Giga Casting & Machining
**Date:** 2026-04-07  **Shift:** B  **Downtime:** 366 min  **Estimated lost vehicles:** 131.4
**Work order:** WO-2026-002693  **Escalation level reached:** L6

## Problem statement
Intermittent GP-SHOT-SLOW over last hour, now hard-stopped. Operator noted warm housing.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor IDRA was engaged.

## Investigation
Arrived 17:05. Checked accumulator pre-charge. Measured hyd_pressure_bar = 260.63 bar (nominal 280, warn 255, alarm 235). Cause: shot sleeve wear.

## Root cause
Shot sleeve wear (category: Wear / aging).

## Corrective actions taken
Inspected shot sleeve and plunger tip.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (current) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Bianca Cox  Due: 2026-04-24
