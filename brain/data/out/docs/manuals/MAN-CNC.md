# Machine Manual: DMG MORI DMU 340 G (5-Axis Machining Center)

**Document ID:** MAN-CNC  |  **Area:** Giga Casting & Machining (CAS)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** CAS-CNC-01, CAS-CNC-02, CAS-CNC-03, CAS-CNC-04
- **Manufacturer / model:** DMG MORI / DMU 340 G
- **Description:** 5-axis machining center for mating surfaces and interface bores on the casting.
- **Typical cycle time:** 420 s
- **Typical replacement value:** about $1,300,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| vibration_mm_s | mm/s | 1.2 | 0.25 | 4.0 | 6.5 |
| motor_current_a | A | 22 | 1.5 | 32 | 38 |
| motor_temp_c | C | 48 | 2 | 72 | 85 |
| coolant_temp_c | C | 22 | 0.8 | 30 | 36 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-CNC-D: Daily check: coolant, lube, air, chip clearing
- Interval: 1 days; typical duration 15 min; trade Mechanical (L1)

### PM-CNC-M: Monthly ballscrew lubrication and filter change
- Interval: 30 days; typical duration 90 min; trade Mechanical (L2)

### PM-CNC-A: Annual geometry check and spindle vibration baseline
- Interval: 365 days; typical duration 300 min; trade Mechanical (L3)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### CNC-SPINDLE-VIB: Spindle vibration above limit
- **Severity:** 3  |  **Typical MTTR:** 180-720 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Spindle bearing wear; Tool imbalance; Drawbar clamp force low
- **Corrective actions:**
  1. Check tool balance and clamp force
  2. Vibration analysis; plan spindle exchange
- **Parts likely needed:** CNC-SPINDLE-EX (Spindle exchange unit)
- **Early-warning signature:** channel `vibration_mm_s` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### CNC-COOL-LOW: Coolant concentration / pressure low
- **Severity:** 1  |  **Typical MTTR:** 20-90 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Concentration drift; Pump wear; Filter loaded
- **Corrective actions:**
  1. Check refractometer reading; adjust concentration
  2. Replace filter bags
- **Parts likely needed:** CNC-FLT-BAG (Coolant filter bag)

### CNC-ATC: Automatic tool changer fault
- **Severity:** 2  |  **Typical MTTR:** 45-240 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Gripper wear; Air pressure low; Position sensor misaligned
- **Corrective actions:**
  1. Check air pressure, gripper fingers
  2. Re-teach ATC positions
- **Parts likely needed:** CNC-GRIP-ATC (ATC gripper set)

### CNC-AXIS-DEV: Axis following error / servo alarm
- **Severity:** 2  |  **Typical MTTR:** 90-420 min  |  **Trade:** Controls / PLC  |  **Code source:** `synthetic`
- **Probable causes:** Ballscrew wear; Encoder fault; Lubrication failure
- **Corrective actions:**
  1. Check lubrication; backlash measurement
  2. Replace encoder / ballscrew nut
- **Parts likely needed:** CNC-ENC-LIN (Linear scale)
- **Early-warning signature:** channel `motor_current_a` shows drift up before failure.

### CNC-PART-OOT: Dimensional drift: part out of tolerance
- **Severity:** 2  |  **Typical MTTR:** 30-150 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Thermal growth; Tool wear; Fixture wear
- **Corrective actions:**
  1. Re-qualify tool offsets; warm-up cycle
  2. Inspect fixture clamping pads

## 7. Symptom-to-cause quick guide

- If `vibration_mm_s` is abnormal, think of: CNC-SPINDLE-VIB (spindle vibration above limit).
- If `motor_current_a` is abnormal, think of: CNC-AXIS-DEV (axis following error / servo alarm).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CNC-ENC-LIN | Linear scale | 1,650 |
| CNC-FLT-BAG | Coolant filter bag | 60 |
| CNC-GRIP-ATC | ATC gripper set | 540 |
| CNC-SPINDLE-EX | Spindle exchange unit | 21,000 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0118  |  Contract: Gold  |  Phone response: 4 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
