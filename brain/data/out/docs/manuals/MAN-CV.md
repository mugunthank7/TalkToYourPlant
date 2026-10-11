# Machine Manual: Duerr EcoProFlex skillet conveyor (Skillet/Overhead Conveyor)

**Document ID:** MAN-CV  |  **Area:** General Assembly (GA)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** M06, GA-CV-02, GA-CV-03
- **Manufacturer / model:** Duerr / EcoProFlex skillet conveyor
- **Description:** Vehicle carrier conveyor with VFD gearmotors.
- **Typical cycle time:** 95 s
- **Typical replacement value:** about $2,900,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| motor_current_a | A | 28 | 1.5 | 40 | 48 |
| vibration_mm_s | mm/s | 1.9 | 0.3 | 5.0 | 8.0 |
| motor_temp_c | C | 55 | 2.5 | 80 | 95 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-CV-W: Weekly chain lubrication and inspection
- Interval: 7 days; typical duration 60 min; trade Mechanical (L1)

### PM-CV-Q: Quarterly gearbox oil and drive alignment
- Interval: 90 days; typical duration 180 min; trade Mechanical (L2)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### CNV-JAM: Carrier jam / zone blocked
- **Severity:** 2  |  **Typical MTTR:** 10-90 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Misaligned carrier; Photo-eye dirty; Chain tension low
- **Corrective actions:**
  1. Clear jam per LOTO
  2. Clean sensors
  3. Check chain tension and track alignment

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

### CNV-ENC-LOSS: Position encoder lost sync
- **Severity:** 1  |  **Typical MTTR:** 20-80 min  |  **Trade:** Controls / PLC  |  **Code source:** `synthetic`
- **Probable causes:** Dirty encoder disc; Loose coupling
- **Corrective actions:**
  1. Clean/inspect encoder
  2. Re-home conveyor
- **Parts likely needed:** CNV-ENC-INC (Incremental encoder)

## 7. Symptom-to-cause quick guide

- If `motor_current_a` is abnormal, think of: CNV-DRV-OVL (drive overload (VFD)).
- If `vibration_mm_s` is abnormal, think of: CNV-CHAIN-STRETCH (chain elongation beyond limit).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CNV-CHAIN-SEC | Drive chain section | 760 |
| CNV-ENC-INC | Incremental encoder | 320 |
| CNV-GMOTOR | Gearmotor 5.5 kW | 1,900 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0120  |  Contract: Premium 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
