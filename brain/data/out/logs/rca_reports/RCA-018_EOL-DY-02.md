# RCA-018: CNC-SPINDLE-VIB: Spindle vibration above limit

**Machine:** EOL-DY-02 (Roll & Brake Dynamometer 2, MAHA Chassis dynamometer AWD) - Area: End-of-Line Test & Release
**Date:** 2025-05-27  **Shift:** B  **Downtime:** 332 min  **Estimated lost vehicles:** 190.8
**Work order:** WO-2025-003651  **Escalation level reached:** L6

## Problem statement
Roll & Brake Dynamometer 2 faulted (CNC-SPINDLE-VIB). Line lead called maintenance via radio at 16:59.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor MAHA was engaged.

## Investigation
Arrived 17:03. Checked tool balance and clamp force. Measured vibration_mm_s = 4.26 mm/s (nominal 1.5, warn 4.5, alarm 7.5). Cause: spindle bearing wear.

## Root cause
Spindle bearing wear (category: Wear / aging).

## Corrective actions taken
Vibration analysis done: analysis; plan spindle exchange.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (temperature) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Anthony Moore  Due: 2025-06-10
