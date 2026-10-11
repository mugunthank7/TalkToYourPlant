# SOP-BAT-03: Pack End-of-Line: Helium Leak Test and HV Test Fail Handling

**Area:** BAT  |  **Owner:** Quality Engineer  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Helium leak test
- Run reference leak check weekly and at the start of each shift on A criticality; reject threshold typically 5 x 10^-6 mbar l/s (warn) and 1 x 10^-5 (alarm) for the plant recipe.
- Failed packs are quarantined, retested once, and sent to rework if still failing. Check seal/gasket, fastening torque history and glue bead record in MES.

## HV / insulation / functional test
- Insulation resistance or functional failure: quarantine the pack in the marked area, inform the HV Safety Engineer if there is any voltage anomaly or swelling.
- False-fail trends (TST-FALSE-FAIL) are investigated for contact wear in the fixture (pogo pins) and threshold drift before touching packs.
- Packs that fail twice go to teardown with Quality; keep the data trace.

## References
- Internal
