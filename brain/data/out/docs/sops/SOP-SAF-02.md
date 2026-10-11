# SOP-SAF-02: High-Voltage (EV Battery) Safe Work Procedure

**Area:** BAT  |  **Owner:** HV Safety Engineer  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Purpose
Control electrical shock, arc-flash and thermal risks when working on EV battery modules, packs and HV test equipment (typically 400 V to 800 V nominal; a pack with ~198 cells in series can operate from roughly 610 to 835 V).

## Qualification
- **NFPA 70E qualified person (cert HV):** may work on or near exposed energized parts only with an approved energized work permit.
- **HVB (non-electrical HV awareness):** may handle sealed, isolated packs and use galvanically isolated fastening tools; may not open HV enclosures.

## Rules
1. Treat every pack as energized. A pack is NOT safe until the **service disconnect** is pulled, the pack is verified at zero volts with a CAT III/IV rated meter on both poles to chassis, and the insulation resistance measurement is recorded.
2. PPE for qualified persons: Class 0 (1000 V) rubber insulating gloves with leather protectors (air-tested before shift), arc-rated face shield and clothing, insulated tools (1000 V rated). Non-qualified persons wear cut-resistant gloves and safety glasses and keep a 1 m exclusion distance from open HV.
3. Fastening tools used near HV busbars must have **galvanically isolated chucks**; never substitute a standard bit or socket.
4. Remove all metal jewelry. No conductive tools on top of open packs. Use dissipative mats.
5. Two-person rule for all HV work; one is the safety observer with the E-stop in hand and trained in rescue (non-conductive hook).
6. Cells outside spec (swelling, odor, leakage, surface temperature > 60 C): STOP, move people out, follow SOP-SAF-03.

## HV test equipment (pack EOL, HV tester)
- Verify interlock loop and warning beacons each shift (daily check PM-BE).
- Discharge and verify zero before connecting/disconnecting leads. Insulation test voltage is applied only when cell door is closed and interlock confirmed.
- A **HV insulation fault** alarm (TST-HV-ISO) stops the test; do not retry more than once without a qualified person inspecting cables for moisture or damage.

## Escalation
Any HV incident or suspected fault is **Level 6 immediately**: page HV Safety Engineer and EHS. Quarantine the pack in the marked battery quarantine bay (outdoors cage, 3 m separation).

## Records
Energized work permits, insulation resistance logs, PPE glove test log, and incident reports.

## References
- NFPA 70E
- OSHA 29 CFR 1910.147
