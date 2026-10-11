# RCA-026: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** CAS-CNC-03 (5-Axis Machining Center 3, DMG MORI DMU 340 G) - Area: Giga Casting & Machining
**Date:** 2025-10-15  **Shift:** A  **Downtime:** 299 min  **Estimated lost vehicles:** 71.9
**Work order:** WO-2025-007530  **Escalation level reached:** L5

## Problem statement
Operator reports: spindle vibration above limit. Machine halted in cycle, alarm CNC-SPINDLE-VIB.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor DMG MORI was engaged.

## Investigation
On site 08:30. Followed troubleshooting steps in the DMG MORI DMU 340 G manual for CNC-SPINDLE-VIB. Measured vibration_mm_s = 3.79 mm/s (nominal 1.2, warn 4.0, alarm 6.5). Found: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
1) Checked tool balance and clamp force. 2) Vibration analysis done: analysis; plan spindle exchange.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (current) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Raymond Cooper  Due: 2025-10-29
