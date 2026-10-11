# RCA-007: ABB-GEAR-NOISE: Abnormal gearbox noise/vibration on axis 3

**Machine:** BIW-WA-02 (Handling/Weld Robot (ABB) 2, ABB IRB 6700-235/2.65) - Area: Body-in-White
**Date:** 2024-12-23  **Shift:** A  **Downtime:** 323 min  **Estimated lost vehicles:** 142.8
**Work order:** WO-2024-002204  **Escalation level reached:** L6

## Problem statement
At 10:49 Handling/Weld Robot (ABB) 2 went down with ABB-GEAR-NOISE. Operator tried reset twice, alarm returned.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor ABB was engaged.

## Investigation
On site 10:51. Followed troubleshooting steps in the ABB IRB 6700-235/2.65 manual for ABB-GEAR-NOISE. Measured vibration_mm_s = 4.36 mm/s (nominal 1.8, warn 4.5, alarm 7.1). Found: reducer wear.

## Root cause
Reducer wear (category: Wear / aging).

## Corrective actions taken
1) Checked oil level and sample oil (Fe ppm). 2) Vibration analysis done: analysis on gearbox.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (current) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Patrick Perez  Due: 2025-01-08
