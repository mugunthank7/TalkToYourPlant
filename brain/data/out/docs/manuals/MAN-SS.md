# Machine Manual: Siemens 15 kV / 480 V substation (HV Substation)

**Document ID:** MAN-SS  |  **Area:** Utilities & Facilities (UTL)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** UTL-SS-01, UTL-SS-02
- **Manufacturer / model:** Siemens / 15 kV / 480 V substation
- **Description:** Medium-voltage substation feeding plant lines.
- **Duty:** continuous
- **Typical replacement value:** about $1,600,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| transformer_temp_c | C | 62 | 3 | 95 | 110 |
| motor_current_a | A | 900 | 40 | 1250 | 1400 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-SS-IR: Quarterly infrared thermography of switchgear
- Interval: 90 days; typical duration 90 min; trade Electrical (L3)

### PM-SS-A: Annual breaker maintenance and relay test
- Interval: 365 days; typical duration 480 min; trade Electrical (L3)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### SS-XFMR-TEMP: Transformer winding temperature high
- **Severity:** 3  |  **Typical MTTR:** 60-300 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Overload; Cooling fan failure
- **Corrective actions:**
  1. Check load; check fans; thermographic scan
- **Parts likely needed:** SS-FAN (Cooling fan set)
- **Early-warning signature:** channel `transformer_temp_c` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### SS-BKR-TRIP: Feeder breaker trip
- **Severity:** 3  |  **Typical MTTR:** 30-240 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Overcurrent; Ground fault
- **Corrective actions:**
  1. Review relay event log; isolate feeder; megger test
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `transformer_temp_c` is abnormal, think of: SS-XFMR-TEMP (transformer winding temperature high).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| SS-FAN | Cooling fan set | 520 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0132  |  Contract: Premium 24/7  |  Phone response: 2 h  |  On-site: 12 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
