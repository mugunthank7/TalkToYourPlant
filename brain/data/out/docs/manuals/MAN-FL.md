# Machine Manual: Duerr EcoFill (Fluid Fill Station)

**Document ID:** MAN-FL  |  **Area:** General Assembly (GA)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** GA-FL-01, GA-FL-02
- **Manufacturer / model:** Duerr / EcoFill
- **Description:** Vacuum fill of coolant, brake fluid and washer fluid.
- **Typical cycle time:** 70 s
- **Typical replacement value:** about $450,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| hyd_pressure_bar | bar | 6 | 0.1 | 5 | 4 |
| vacuum_mbar | mbar | 20 | 1 | 40 | 80 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-FL-M: Monthly vacuum pump oil check, hose inspection
- Interval: 30 days; typical duration 60 min; trade Mechanical (L1)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### TST-CAL-FAIL: Self-calibration failed / reference out of tolerance
- **Severity:** 2  |  **Typical MTTR:** 30-240 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Sensor drift; Contaminated fixtures
- **Corrective actions:**
  1. Run reference artefact; recalibrate; replace sensor
- **Parts likely needed:** TST-SNSR-REF (Reference sensor kit)

### TST-COMM: Test station communication loss to MES
- **Severity:** 2  |  **Typical MTTR:** 10-60 min  |  **Trade:** Controls / PLC  |  **Code source:** `synthetic`
- **Probable causes:** Network switch port; Service crash
- **Corrective actions:**
  1. Restart service; replace patch cable/switch port

### TST-FALSE-FAIL: Elevated false-fail rate
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Contact wear in test fixture; Environmental noise; Software threshold drift
- **Corrective actions:**
  1. Inspect pogo pins/contacts
  2. Run gauge R&R
  3. Review thresholds with process engineer
- **Parts likely needed:** TST-POGO (Pogo pin contact set)

## 7. Symptom-to-cause quick guide

- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| TST-POGO | Pogo pin contact set | 480 |
| TST-SNSR-REF | Reference sensor kit | 1,300 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0120  |  Contract: Premium 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
