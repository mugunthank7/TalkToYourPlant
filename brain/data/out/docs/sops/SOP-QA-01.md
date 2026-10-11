# SOP-QA-01: Torque NOK Handling and Tool Calibration (General Assembly)

**Area:** GA  |  **Owner:** Quality Engineer  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

- Atlas Copco Power Focus controllers log each tightening with VIN, torque, angle and status.
- NOK actions: stop the station, inspect fastener and joint, **do not re-tighten** without quality approval, and check the daily test joint verification.
- Three NOKs in a row, or 2% NOK rate in a shift, triggers a containment: check tool calibration, socket wear, and fastener batch; quarantine suspect lots; audit the last 20 vehicles.
- Calibration: transducer calibration every 12 months or 500k cycles; overdue tools are tagged out (TQ-CAL-DUE).
- Cable faults (TQ-CBL-FAULT) and tool overtemperature (TQ-MOTOR-TEMP) are handled by process technicians.

## References
- Internal
