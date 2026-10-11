# RCA-048: PRS-CLUTCH: Servo drive overload / main motor overtemperature

**Machine:** STP-PRS-03 (Servo Press 3, Schuler MSP 2000 servo press) - Area: Stamping
**Date:** 2026-06-29  **Shift:** C  **Downtime:** 352 min  **Estimated lost vehicles:** 212.7
**Work order:** WO-2026-005063  **Escalation level reached:** L6

## Problem statement
PRS-CLUTCH displayed on HMI; Servo Press 3 stopped after a die/tool change. Andon pulled at 23:03.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor Schuler was engaged.

## Investigation
On site 23:07. Followed troubleshooting steps in the Schuler MSP 2000 servo press manual for PRS-CLUTCH. Found: duty cycle.

## Root cause
Duty cycle (category: Thermal / cooling).

## Corrective actions taken
1) Checked cooling; check motor current profile.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (vibration) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Hector Powell  Due: 2026-07-13
