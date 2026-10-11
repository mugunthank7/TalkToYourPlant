# RCA-013: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** CAS-CNC-04 (5-Axis Machining Center 4, DMG MORI DMU 340 G) - Area: Giga Casting & Machining
**Date:** 2025-03-18  **Shift:** A  **Downtime:** 404 min  **Estimated lost vehicles:** 135.1
**Work order:** WO-2025-001910  **Escalation level reached:** L6

## Problem statement
Intermittent CNC-SPINDLE-VIB over last hour, now hard-stopped. Operator noted reject rate creeping up.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor DMG MORI was engaged.

## Investigation
On site 11:52. Followed troubleshooting steps in the DMG MORI DMU 340 G manual for CNC-SPINDLE-VIB. Measured vibration_mm_s = 3.21 mm/s (nominal 1.2, warn 4.0, alarm 6.5). Found: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
1) Checked tool balance and clamp force.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Nicholas Gutierrez  Due: 2025-04-13
