# RCA-004: GP-TIEBAR: Tie-bar load imbalance: clamping force deviation across 4 tie bars

**Machine:** CAS-GP-01 (Giga Press 1, IDRA GIGAPRESS NEO 6100) - Area: Giga Casting & Machining
**Date:** 2024-11-29  **Shift:** C  **Downtime:** 294 min  **Estimated lost vehicles:** 114.7
**Work order:** WO-2024-001583  **Escalation level reached:** L6

## Problem statement
Alarm GP-TIEBAR - tie-bar load imbalance: clamping force deviation across 4 tie bars. Downstream no immediate impact (buffer ok).

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor IDRA was engaged.

## Investigation
Arrived 05:03. Ran Block-Control tie-bar calibration. Measured vibration_mm_s = 4.21 mm/s (nominal 2.1, warn 5.0, alarm 8.0). Cause: toggle lubrication lack.

## Root cause
Toggle lubrication lack (category: Lubrication).

## Corrective actions taken
Ran Block-Control tie-bar calibration.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (temperature) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Lena Moore  Due: 2025-01-01
