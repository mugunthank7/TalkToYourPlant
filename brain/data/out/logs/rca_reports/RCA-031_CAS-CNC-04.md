# RCA-031: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** CAS-CNC-04 (5-Axis Machining Center 4, DMG MORI DMU 340 G) - Area: Giga Casting & Machining
**Date:** 2026-01-21  **Shift:** C  **Downtime:** 486 min  **Estimated lost vehicles:** 120.1
**Work order:** WO-2026-000577  **Escalation level reached:** L6

## Problem statement
Alarm CNC-SPINDLE-VIB - spindle vibration above limit. Downstream no immediate impact (buffer ok).

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor DMG MORI was engaged.

## Investigation
Arrived 05:51. Checked tool balance and clamp force. Measured vibration_mm_s = 3.62 mm/s (nominal 1.2, warn 4.0, alarm 6.5). Cause: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
Checked tool balance and clamp force.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (current) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Jin Holm  Due: 2026-02-10
