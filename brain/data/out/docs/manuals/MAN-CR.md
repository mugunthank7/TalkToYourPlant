# Machine Manual: Konecranes CXT 20 t (Overhead Crane)

**Document ID:** MAN-CR  |  **Area:** Intralogistics (LOG)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** LOG-CR-01, LOG-CR-02, LOG-CR-03
- **Manufacturer / model:** Konecranes / CXT 20 t
- **Description:** Overhead cranes for die and heavy component handling.
- **Duty:** continuous
- **Typical replacement value:** about $380,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| motor_current_a | A | 40 | 3 | 60 | 75 |
| vibration_mm_s | mm/s | 1.5 | 0.25 | 4.5 | 7.0 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-CR-M: Monthly brake and wire rope inspection (OSHA 1910.179)
- Interval: 30 days; typical duration 90 min; trade Mechanical (L2)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### CNV-DRV-OVL: Drive overload (VFD)
- **Severity:** 2  |  **Typical MTTR:** 45-240 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Bearing seizure; Chain tight; Motor winding degradation
- **Corrective actions:**
  1. Check mechanical free movement
  2. Check motor current vs. nameplate
  3. Replace gearmotor if abnormal
- **Parts likely needed:** CNV-GMOTOR (Gearmotor 5.5 kW)
- **Early-warning signature:** channel `motor_current_a` shows drift up before failure.

### CNV-CHAIN-STRETCH: Chain elongation beyond limit
- **Severity:** 2  |  **Typical MTTR:** 120-480 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Wear / lack of lubrication
- **Corrective actions:**
  1. Measure elongation (>3% replace)
  2. Lubricate; replace chain section
- **Parts likely needed:** CNV-CHAIN-SEC (Drive chain section)
- **Early-warning signature:** channel `vibration_mm_s` shows drift up before failure.

## 7. Symptom-to-cause quick guide

- If `motor_current_a` is abnormal, think of: CNV-DRV-OVL (drive overload (VFD)).
- If `vibration_mm_s` is abnormal, think of: CNV-CHAIN-STRETCH (chain elongation beyond limit).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CNV-CHAIN-SEC | Drive chain section | 760 |
| CNV-GMOTOR | Gearmotor 5.5 kW | 1,900 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0134  |  Contract: Gold  |  Phone response: 4 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
