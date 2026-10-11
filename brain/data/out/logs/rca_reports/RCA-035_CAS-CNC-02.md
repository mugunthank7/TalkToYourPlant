# RCA-035: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** CAS-CNC-02 (5-Axis Machining Center 2, DMG MORI DMU 340 G) - Area: Giga Casting & Machining
**Date:** 2026-02-10  **Shift:** C  **Downtime:** 419 min  **Estimated lost vehicles:** 149.1
**Work order:** WO-2026-001104  **Escalation level reached:** L6

## Problem statement
Intermittent CNC-SPINDLE-VIB over last hour, now hard-stopped. Operator noted reject rate creeping up.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor DMG MORI was engaged.

## Investigation
Arrived 03:34. Checked tool balance and clamp force. Measured vibration_mm_s = 3.63 mm/s (nominal 1.2, warn 4.0, alarm 6.5). Cause: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
Vibration analysis done: analysis; plan spindle exchange.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Paul Barnes  Due: 2026-03-15
