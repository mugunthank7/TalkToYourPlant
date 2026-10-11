# Machine Manual: Chroma Battery pack EOL test system (Pack End-of-Line HV Tester)

**Document ID:** MAN-BE  |  **Area:** Battery Pack Assembly (BAT)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** BAT-BE-01, BAT-BE-02
- **Manufacturer / model:** Chroma / Battery pack EOL test system
- **Description:** High-voltage pack functional and insulation test (up to 1000 V).
- **Typical cycle time:** 180 s
- **Typical replacement value:** about $520,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Battery area: HV rules in SOP-SAF-02; thermal event response in SOP-SAF-03; use isolated tools only.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| coolant_temp_c | C | 24 | 0.5 | 30 | 35 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-BE-M: Monthly HV safety interlock and insulation tester verification
- Interval: 30 days; typical duration 90 min; trade Electrical (L2)

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

### TST-HV-ISO: Insulation resistance fault on HV test circuit
- **Severity:** 3  |  **Typical MTTR:** 60-300 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Moisture ingress; Cable damage
- **Corrective actions:**
  1. De-energize per HV procedure; inspect cables; megger test
- **Parts likely needed:** TST-HV-CBL (HV test cable assembly)
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| TST-HV-CBL | HV test cable assembly | 890 |
| TST-POGO | Pogo pin contact set | 480 |
| TST-SNSR-REF | Reference sensor kit | 1,300 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0126  |  Contract: Standard  |  Phone response: 8 h  |  On-site: 72 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
