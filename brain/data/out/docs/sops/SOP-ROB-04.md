# SOP-ROB-04: Spot Weld Tip Dressing, Weld Quality Verification and Weld Gun Care

**Area:** BIW  |  **Owner:** Process Engineer  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Tip care
- Dress or change electrode caps at the programmed stepper count (typically every 16-100 welds depending on coating and schedule).
- Cooling water flow at each gun must be at least 4 l/min; low flow causes tip overheating and sticking (fault codes WG-TIP-WEAR, KSS-SPOT-STICK).
- If a tip sticks (robot motion blocked), break the tip free using the manual release, replace the cap, and check the weld schedule and flow before resuming.

## Verification
- Peel test (chisel/destructive) at start of each shift per weld group; nugget diameter at least 4 x sqrt(t) where t is thinnest sheet thickness.
- Ultrasonic nugget testing for critical structural welds weekly.
- Any gun with low-current alerts (weld current falling below warn) is inspected for cable/shunt wear and transformer cooling.

## Weld transformer overtemperature (WG-TRANSF-TEMP)
Check coolant flow and temperature; verify duty cycle; check thermal switch; do not defeat the switch. Replace the transformer if windings are suspect.

## Records
Peel test log, tip dress logs (auto), weld controller logs.

## References
- Internal
