# RCA-045: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** EOL-DY-03 (Roll & Brake Dynamometer 3, MAHA Chassis dynamometer AWD) - Area: End-of-Line Test & Release
**Date:** 2026-05-15  **Shift:** C  **Downtime:** 514 min  **Estimated lost vehicles:** 316.2
**Work order:** WO-2026-003735  **Escalation level reached:** L6

## Problem statement
Alarm CNC-SPINDLE-VIB - spindle vibration above limit. Downstream line is blocked.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor MAHA was engaged.

## Investigation
Arrived 04:39. Checked tool balance and clamp force. Measured vibration_mm_s = 3.84 mm/s (nominal 1.5, warn 4.5, alarm 7.5). Cause: spindle bearing wear.

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
Owner: Paul Barnes  Due: 2026-06-07
