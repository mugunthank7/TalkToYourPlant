# RCA-051: CNV-CHAIN-STRETCH: Chain elongation beyond limit

**Machine:** GA-CV-02 (Skillet/Overhead Conveyor 2, Duerr EcoProFlex skillet conveyor) - Area: General Assembly
**Date:** 2026-08-05  **Shift:** C  **Downtime:** 307 min  **Estimated lost vehicles:** 147.1
**Work order:** WO-2026-006103  **Escalation level reached:** L6

## Problem statement
CNV-CHAIN-STRETCH displayed on HMI; Skillet/Overhead Conveyor 2 stopped at part pickup. Andon pulled at 04:15.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor Duerr was engaged.

## Investigation
Arrived 04:20. Measured elongation (>3% replace). Measured vibration_mm_s = 5.19 mm/s (nominal 1.9, warn 5.0, alarm 8.0). Cause: wear / lack of lubrication.

## Root cause
Wear / lack of lubrication (category: Lubrication).

## Corrective actions taken
Lubricate; replace chain section.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (temperature) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Matthew Okafor  Due: 2026-08-21
