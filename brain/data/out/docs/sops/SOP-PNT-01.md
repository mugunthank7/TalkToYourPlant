# SOP-PNT-01: Paint Booth: Ex-Zone Safety, Purge Faults, Atomizer and Color Changer

**Area:** PNT  |  **Owner:** Paint Area Manager  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Hazard
Paint robots operate in explosion-protected zones; purged enclosures must maintain positive pressure before power is applied.

## Purge fault (PR-EXPL-INTERLOCK) - Level 6 notification
1. **Do not start or reset the robot repeatedly.** Shut down the booth segment via the booth control.
2. Verify purge air supply pressure and flow; check the purge pressure sensor and tubing for kinks/leaks.
3. Only a person with ATEX competence (cert ATEX) may restore; document readings before restart.

## Atomizer (PR-BELL-SPEED)
- Bell speed nominal ~45 krpm; warn at 42, alarm at 38. Check turbine air pressure and filter, bearing air quality, and contamination on the cup.
- Replace the turbine at alarm or when speed fluctuates > 3%.
- Verify film build on test panel after replacement.

## Color changer
Flush with solvent per color change; stuck valves are common after long idle periods. Replace valve seats and run a purge test.

## Film build defects (PR-FILM-DEFECT)
Calibrate flow meters, check shaping air, and run test panels; confirm thickness with the thickness gauge before releasing production.

## Housekeeping
Overspray and booth filters are replaced per PM; keep walkways clear.

## References
- NFPA 33
