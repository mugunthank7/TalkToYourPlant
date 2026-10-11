# Machine Manual: MAHA Chassis dynamometer AWD (Roll & Brake Dynamometer)

**Document ID:** MAN-DY  |  **Area:** End-of-Line Test & Release (EOL)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** EOL-DY-01, EOL-DY-02, EOL-DY-03
- **Manufacturer / model:** MAHA / Chassis dynamometer AWD
- **Description:** AWD roller test stand for drivetrain, brake and regen test.
- **Typical cycle time:** 180 s
- **Typical replacement value:** about $950,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| vibration_mm_s | mm/s | 1.5 | 0.25 | 4.5 | 7.5 |
| motor_current_a | A | 60 | 4 | 95 | 120 |
| motor_temp_c | C | 50 | 2.5 | 80 | 95 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-DY-W: Weekly roller surface and bearing check
- Interval: 7 days; typical duration 45 min; trade Mechanical (L1)

### PM-DY-A: Annual calibration of speed and force sensors
- Interval: 365 days; typical duration 240 min; trade Process / Quality (L2)

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

### CNC-SPINDLE-VIB: Spindle vibration above limit
- **Severity:** 3  |  **Typical MTTR:** 180-720 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Spindle bearing wear; Tool imbalance; Drawbar clamp force low
- **Corrective actions:**
  1. Check tool balance and clamp force
  2. Vibration analysis; plan spindle exchange
- **Parts likely needed:** CNC-SPINDLE-EX (Spindle exchange unit)
- **Early-warning signature:** channel `vibration_mm_s` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `vibration_mm_s` is abnormal, think of: CNC-SPINDLE-VIB (spindle vibration above limit).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CNC-SPINDLE-EX | Spindle exchange unit | 21,000 |
| TST-HV-CBL | HV test cable assembly | 890 |
| TST-POGO | Pogo pin contact set | 480 |
| TST-SNSR-REF | Reference sensor kit | 1,300 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0129  |  Contract: Standard  |  Phone response: 8 h  |  On-site: 48 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
