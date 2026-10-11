# SOP-CAS-01: Giga Press Start-up, Shutdown and Daily Hydraulic Checks

**Area:** CAS  |  **Owner:** Casting Area Manager  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Machine overview
IDRA GIGAPRESS NEO 6100 class: 6,100 t (about 60,000 kN) clamping force, die height 2,400 mm, ~430 t, with accumulator-based injection (fill time roughly 120 ms for a 6,000 t class machine), Block-Control tie-bar monitoring with automatic clamping-force adjustment, automatic toggle lubrication and servo-driven guarding.

## Start-up
1. Verify LOTO released and the machine area clear. Check the die is locked and cooling circuits are connected.
2. Hydraulic walk-down: reservoir level at least 85%, oil temperature between 35 and 50 C, no leaks, filter dP indicators green, accumulator pre-charge gauges within the setpoint on the machine card.
3. Start hydraulic pumps, wait for pressure to stabilize at setpoint (nominal ~280 bar on the main circuit). If pressure fails to build or is more than 10% low, stop (fault GP-PRESS-LOW).
4. Warm up die with the die thermal control units to the die temperature recipe before first shot. Run 3 dry cycles and check clamping force distribution across the four tie bars; investigate a deviation > 3% (fault GP-TIEBAR, run tie-bar calibration).
5. Start the dosing furnace transfer and inject the first shots at reduced speed; verify fill time and shot curve against the golden profile before full speed.

## During production
- Check the shot profile each shift: a slow fill or low accumulator recovery points to accumulator pre-charge loss, valve response issues or sleeve wear (GP-SHOT-SLOW).
- Record hydraulic temperature; above 58 C is a warn. Clean oil cooler and check water flow; above 65 C is an alarm: stop at end of shot.
- Trim, X-ray and machining cells downstream depend on this machine (criticality A).

## Shutdown
Run last shot, retract plunger, close die with low force, switch off pumps, vent accumulators only for maintenance (LOTO). Record the shot counter and any parameter changes.

## References
- IDRA public Giga Press catalog data
