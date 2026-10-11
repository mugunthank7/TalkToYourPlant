# SOP-UTL-01: Compressed Air System: Compressor Trip and Low Pressure Response

**Area:** UTL  |  **Owner:** Utilities Supervisor  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

- Plant air header normal 7.5 bar; if pressure falls below 6.0 bar start the standby compressor and prepare to shed non-critical loads (blow-off, cleaning).
- **Discharge temperature high (CMP-DISCH-TEMP):** nominal ~85 C; warn 100 C; alarm 108 C. Check cooler fouling (Texas summer), oil level and thermostatic valve; clean cooler fins; check ambient ventilation.
- **Oil separator dP high:** replace separator element (typically at 0.9 bar differential).
- **Dryer dew point alarm:** check condensate drains; service dryer.
- **Motor overload trip:** check bearings and supply voltage imbalance.
- Run the lead/lag schedule weekly so run hours stay balanced across the four compressors.

## References
- Internal
