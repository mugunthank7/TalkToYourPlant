# RCA-055: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** EOL-DY-01 (Roll & Brake Dynamometer 1, MAHA Chassis dynamometer AWD) - Area: End-of-Line Test & Release
**Date:** 2026-09-03  **Shift:** A  **Downtime:** 454 min  **Estimated lost vehicles:** 145.4
**Work order:** WO-2026-006937  **Escalation level reached:** L6

## Problem statement
CNC-SPINDLE-VIB displayed on HMI; Roll & Brake Dynamometer 1 stopped after a die/tool change. Andon pulled at 11:56.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor MAHA was engaged.

## Investigation
On site 11:58. Followed troubleshooting steps in the MAHA Chassis dynamometer AWD manual for CNC-SPINDLE-VIB. Measured vibration_mm_s = 4.56 mm/s (nominal 1.5, warn 4.5, alarm 7.5). Found: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
1) Checked tool balance and clamp force. 2) Vibration analysis done: analysis; plan spindle exchange.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: James Thompson  Due: 2026-10-08
