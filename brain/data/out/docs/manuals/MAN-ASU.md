# Machine Manual: Duerr EcoSupply (Air Supply Unit)

**Document ID:** MAN-ASU  |  **Area:** Paint Shop (PNT)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** PNT-ASU-01, PNT-ASU-02
- **Manufacturer / model:** Duerr / EcoSupply
- **Description:** Booth air conditioning supply.
- **Duty:** continuous
- **Typical replacement value:** about $1,800,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| motor_current_a | A | 55 | 2 | 70 | 80 |
| vibration_mm_s | mm/s | 2.2 | 0.3 | 5.0 | 8.0 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-ASU-M: Monthly filter dP and humidifier check
- Interval: 30 days; typical duration 90 min; trade Mechanical (L1)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### OVN-FAN-VIB: Recirculation fan high vibration
- **Severity:** 3  |  **Typical MTTR:** 120-480 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Bearing wear; Fan imbalance from deposits
- **Corrective actions:**
  1. Vibration measurement; clean impeller
  2. Replace bearings; rebalance
- **Parts likely needed:** OVN-BRG-FAN (Fan bearing set)
- **Early-warning signature:** channel `vibration_mm_s` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### OVN-EXH-LOW: Exhaust flow low (safety interlock)
- **Severity:** 3  |  **Typical MTTR:** 45-240 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Damper stuck; Duct fouled
- **Corrective actions:**
  1. Inspect damper actuator
  2. Clean exhaust duct
- **Parts likely needed:** OVN-DMP-ACT (Damper actuator)
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `vibration_mm_s` is abnormal, think of: OVN-FAN-VIB (recirculation fan high vibration).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| OVN-BRG-FAN | Fan bearing set | 640 |
| OVN-DMP-ACT | Damper actuator | 520 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0120  |  Contract: Premium 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
