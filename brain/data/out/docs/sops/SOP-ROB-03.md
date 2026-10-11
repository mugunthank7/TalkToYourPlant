# SOP-ROB-03: KUKA Maintenance Reminders and Gear Oil Change

**Area:** ALL  |  **Owner:** Robotics Supervisor  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Background
KUKA KRC4/KR C5 controllers raise maintenance reminder messages based on operating hours or calendar time. Typical OEM intervals: gearbox oil replacement every 10,000-20,000 hours or 3-4 years for main axes (A1-A3), inline-wrist belt inspection/tension at 8,000-10,000 h (6-axis inline wrist only), electrical cabinet inspection by calendar. Newer KR QUANTEC PA palletizers specify an oil change at 20,000 operating hours; some models list "20,000 hourly / 5 yearly gear oil change".
Approved lubricant: KUKA-approved synthetic gear oil, ISO VG 150 (for example Shell Tivela S150 on QUANTEC primary axes; about 8 L per primary axis, confirm the exact quantity in the model manual).

## Oil change procedure (summary)
1. **Burn hazard:** if the robot has just stopped, oil and surfaces may be very hot. Let it cool to a safe temperature but drain while still warm for best flow.
2. Lock out the robot (SOP-SAF-01) and block axis 2/3 against falling.
3. Pull out the oil drain hose; place a suitable receptacle under it; unscrew the union nut of the drain hose.
4. Drain completely; inspect the drained oil for metal particles (indicator of internal wear); photograph and record.
5. Refit the hose, refill through the filler port with approved oil to the level mark, replace sealing washers.
6. Run the robot through the warm-up program (axes 1-3 at 50% for 15 minutes), re-check level and leaks.
7. **Reset the maintenance counter** from the SmartPAD (Maintenance > Resets) and record the service date and hours on the WO.

## Related checks
Inspect robot arm housing for oil leakage at the gearbox seals (A1-A3 primary, A4-A6 secondary). A leak that returns within one shift indicates seal wear or an over-filled/blocked-vent gearbox. Brake test on all axes after oil changes.

## References
- Public KUKA maintenance information (industrialmonitordirect.com, kuka.com press release 2021, MaintainX asset library)
