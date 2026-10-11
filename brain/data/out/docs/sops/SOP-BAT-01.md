# SOP-BAT-01: Pack Fastening, Torque Traceability and Isolated Tooling

**Area:** BAT  |  **Owner:** Process Engineer  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Equipment
Synchronous four-spindle fastening stations (Desoutter) apply up to 20 Nm to fix the pack at four points simultaneously; the spindles are galvanically isolated to protect workers near HV busbars. Corded isolated angle drivers are used for busbar rework.

## Procedure
1. Daily torque verification on the test joint (record in the daily check). Reject the station if the verification falls outside +/- 5%.
2. All tightening results are recorded against the VIN/pack serial. NOK results are not re-tightened without quality approval.
3. A **missed-bolt (TQ-BATCH-MISS)** event quarantines the pack, and requires re-inspection by a quality inspector before release.
4. Inspect isolation of chucks and cables at each PM; replace damaged cables (TQ-CBL-FAULT).
5. Transducer calibration yearly (or every 500k cycles); station without valid certificate must not run.

## Typical torque faults
- TQ-NOK: out-of-window torque - check cross-threading, socket wear, transducer drift and fastener lot friction.
- TQ-MOTOR-TEMP: tool temperature rising - verify duty cycle, replace gear head if abnormal.

## References
- Public Desoutter/Assembly magazine information on EV pack fastening
