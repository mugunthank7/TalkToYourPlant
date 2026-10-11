# SOP-GA-01: Conveyor, AGV and AMR Fault Response

**Area:** GA  |  **Owner:** General Assembly Area Manager  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

- **Conveyor jam (CNV-JAM):** LOTO before clearing; check carrier alignment, photo-eye cleanliness and chain tension.
- **Drive overload (CNV-DRV-OVL):** check for mechanical resistance, motor current vs nameplate; replace gearmotor if abnormal; vibration above 5 mm/s is a warn.
- **Chain elongation:** measure elongation, replace the chain section above 3%.
- **AGV/AMR localization lost (AGV-NAV-LOST):** re-localize at a charging station; update map if layout changed.
- **Safety scanner fault (AGV-LIDAR):** clean lens, verify protective field with test object; never bypass.
- **Low battery or charge contact failure:** replace contact set; verify charger.
- Decking AGVs carrying battery packs: a stopped AGV in the marriage station blocks the line (criticality A). Notify the supervisor immediately.

## References
- Internal
