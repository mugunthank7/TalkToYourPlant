# SOP-PNT-02: Cure Oven Start-up, Purge and Temperature Profiling

**Area:** PNT  |  **Owner:** Paint Area Manager  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

1. Start the exhaust fans and verify flow switches (OVN-EXH-LOW interlock prevents burner start).
2. Complete the pre-ignition purge cycle per NFPA 86 timing; confirm the purge timer completes.
3. Ramp the oven zones per recipe (nominal 165 C for cure zones; allowed deviation +/- 5 C).
4. Run a temperature profile with a data logger weekly (and after any burner/fan repair).
5. Alarms: zone temperature deviation (OVN-ZONE-TEMP) - compare with reference thermocouple; fan vibration high (OVN-FAN-VIB) - stop at alarm (vibration > 7.1 mm/s equivalent) and inspect bearings; chain drive faults inside the oven (OVN-CHAIN) - check chain tension hot and relubricate with high-temperature lubricant.
6. Annual: safety interlock test and thermocouple calibration.

## References
- NFPA 86
