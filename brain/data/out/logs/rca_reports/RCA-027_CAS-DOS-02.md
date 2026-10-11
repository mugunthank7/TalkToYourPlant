# RCA-027: DOS-HEATER: Heating element failure

**Machine:** CAS-DOS-02 (Dosing Furnace 2, Striko Westofen Dosing furnace 12t holding) - Area: Giga Casting & Machining
**Date:** 2025-10-21  **Shift:** A  **Downtime:** 682 min  **Estimated lost vehicles:** 269.6
**Work order:** WO-2025-007705  **Escalation level reached:** L6

## Problem statement
DOS-HEATER displayed on HMI; Dosing Furnace 2 stopped during start-up. Andon pulled at 10:27.

## Containment
Line lead isolated the machine and rerouted material where possible. Maintenance supervisor was informed per the escalation matrix; vendor Striko Westofen was engaged.

## Investigation
Initial check 10:32, Dosing Furnace 2 fault DOS-HEATER confirmed. Measured furnace_power_kw = 269.41 kW (nominal 210, warn 260, alarm 300). Probable cause element aging.

## Root cause
Element aging (category: Wear / aging).

## Corrective actions taken
Replaced element; check refractory.

## Preventive actions
- Review PM interval for related tasks and add checklist step for early detection.
- Evaluate condition-monitoring sensor (pressure) alert threshold for earlier warning.
- Verify spare parts stock for the affected component.
- Share lessons learned at the weekly reliability meeting.

## Follow-up
Owner: Vikram Johnson  Due: 2025-11-24
