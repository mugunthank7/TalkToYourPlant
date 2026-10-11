# RCA-025: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** CAS-CNC-04 (5-Axis Machining Center 4, DMG MORI DMU 340 G) - Area: Giga Casting & Machining
**Date:** 2025-08-27  **Shift:** C  **Downtime:** 409 min  **Estimated lost vehicles:** 61.5
**Work order:** WO-2025-006102  **Escalation level reached:** L6

## Problem statement
At 03:55 5-Axis Machining Center 4 went down with CNC-SPINDLE-VIB. Operator tried reset twice, alarm returned.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor DMG MORI was engaged.

## Investigation
On site 04:07. Followed troubleshooting steps in the DMG MORI DMU 340 G manual for CNC-SPINDLE-VIB. Measured vibration_mm_s = 3.25 mm/s (nominal 1.2, warn 4.0, alarm 6.5). Found: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
1) Checked tool balance and clamp force. 2) Vibration analysis done: analysis; plan spindle exchange.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Gerald Williams  Due: 2025-09-22
