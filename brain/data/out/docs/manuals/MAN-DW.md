# Machine Manual: Aumann Hairpin winding line (Hairpin Stator Winding Cell)

**Document ID:** MAN-DW  |  **Area:** Drive Unit / E-Axle (DRV)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** DRV-DW-01, DRV-DW-02
- **Manufacturer / model:** Aumann / Hairpin winding line
- **Description:** Hairpin forming, insertion, and welding of e-motor stators.
- **Typical cycle time:** 55 s
- **Typical replacement value:** about $4,800,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| vibration_mm_s | mm/s | 1.4 | 0.25 | 4.2 | 7.0 |
| motor_current_a | A | 30 | 2 | 45 | 55 |
| coolant_temp_c | C | 24 | 0.5 | 30 | 35 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-DW-M: Monthly tooling wear check and lubrication
- Interval: 30 days; typical duration 120 min; trade Mechanical (L2)

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

### LSR-PWR-LOW: Laser output power below tolerance (measured vs. commanded)
- **Severity:** 3  |  **Typical MTTR:** 30-240 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Protective glass contaminated; Diode module degradation; Fiber connector contamination
- **Corrective actions:**
  1. Inspect/replace protective glass
  2. Clean fiber end-face
  3. Run power measurement; schedule diode module service
- **Parts likely needed:** LSR-PROT-GLASS (Protective cover glass (box 10))
- **Early-warning signature:** channel `laser_power_pct` shows drift down before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `motor_current_a` is abnormal, think of: CNV-DRV-OVL (drive overload (VFD)).
- If `vibration_mm_s` is abnormal, think of: CNV-CHAIN-STRETCH (chain elongation beyond limit).
- If `laser_power_pct` is abnormal, think of: LSR-PWR-LOW (laser output power below tolerance (measured vs. commanded)).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CNV-CHAIN-SEC | Drive chain section | 760 |
| CNV-ENC-INC | Incremental encoder | 320 |
| CNV-GMOTOR | Gearmotor 5.5 kW | 1,900 |
| LSR-PROT-GLASS | Protective cover glass (box 10) | 180 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0127  |  Contract: Gold  |  Phone response: 4 h  |  On-site: 48 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
