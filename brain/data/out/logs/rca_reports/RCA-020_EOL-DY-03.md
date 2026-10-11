# RCA-020: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** EOL-DY-03 (Roll & Brake Dynamometer 3, MAHA Chassis dynamometer AWD) - Area: End-of-Line Test & Release
**Date:** 2025-06-18  **Shift:** B  **Downtime:** 304 min  **Estimated lost vehicles:** 111.1
**Work order:** WO-2025-004193  **Escalation level reached:** L6

## Problem statement
Alarm CNC-SPINDLE-VIB - spindle vibration above limit. Downstream line is blocked.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor MAHA was engaged.

## Investigation
On site 15:23. Followed troubleshooting steps in the MAHA Chassis dynamometer AWD manual for CNC-SPINDLE-VIB. Measured vibration_mm_s = 4.54 mm/s (nominal 1.5, warn 4.5, alarm 7.5). Found: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
1) Checked tool balance and clamp force.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Olivia Ramirez  Due: 2025-07-29
