# SOP-HYD-01: Hydraulic System Fault Response: Low Pressure, High Temperature, Leaks, Filter dP

**Area:** ALL  |  **Owner:** Hydraulics Technician Lead  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## General
Hydraulic systems on presses, the Giga Press and trim press store energy in accumulators. Always depressurize and LOTO before opening any hose, fitting, filter or valve.

## Low pressure
1. Confirm gauge vs transducer; check reservoir level and pump motor current.
2. Check accumulator nitrogen pre-charge (should be 60-70% of minimum operating pressure); recharge or replace bladder/piston seals.
3. Check pump delivery vs baseline and case-drain flow (a rising drain flow indicates pump wear).
4. Inspect valve block cartridges for internal leakage; swap in a known good cartridge if available.
5. Replace suction strainer if clogged; check oil viscosity.

## High oil temperature
Check cooling water flow and inlet temperature, clean the cooler, verify the thermostatic valve, and trend temperature versus cycle count. A steady rise at constant load often indicates pump internal leakage (energy converting to heat).

## Hose/fitting leaks
Isolate and depressurize per LOTO; replace hose with the same part number and date code, torque fitting to spec, clean up spills (SOP-ENV-01), top up reservoir with the correct oil grade; run and inspect under pressure from a safe distance.

## Filters
Replace return and pressure filters at amber dP indicator or at the PM interval; take an oil sample if the filter loaded abnormally fast. Target cleanliness ISO 4406 17/15/12 or better for proportional/servo valves.

## Escalation
Pressure or temperature in alarm, oil fire risk, or a leak larger than 5 gallons: page the Maintenance Supervisor and EHS.

## References
- ISO 4406
