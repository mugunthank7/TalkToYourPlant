# Machine Manual: ABB IRB 6700-235/2.65 (Handling/Weld Robot (ABB))

**Document ID:** MAN-WA  |  **Area:** Body-in-White (BIW)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** BIW-WA-01, BIW-WA-02, BIW-WA-03, BIW-WA-04
- **Manufacturer / model:** ABB / IRB 6700-235/2.65
- **Description:** Heavy payload robot for body framing and part handling.
- **Typical cycle time:** 60 s
- **Typical replacement value:** about $115,000 per unit

## 2. Verified public reference facts

- OEM PM intervals quoted for ABB: about 10,000 operating hours for full PM; ISO 10218 requires periodic safety verification. (source: https://oxmaint.com/industries/manufacturing-plant/industrial-robot-maintenance-checklist-complete)

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Robot cell entry only per SOP-SAF-04; T1 mode, enabling switch in hand.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| motor_current_a | A | 18.0 | 1.2 | 26.0 | 32.0 |
| motor_temp_c | C | 52.0 | 2.5 | 78.0 | 90.0 |
| gearbox_temp_c | C | 48.0 | 2.0 | 70.0 | 82.0 |
| vibration_mm_s | mm/s | 1.8 | 0.3 | 4.5 | 7.1 |
| battery_voltage_v | V | 3.6 | 0.02 | 3.1 | 2.6 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-A-W: Weekly visual check of axes, cabling and tooling
- Interval: 250 operating hours; typical duration 25 min; trade Robotics (L1)
- Steps:
  1. Visual check
  2. Leak check
  3. Check emergency stop functions

### PM-A-M: Quarterly oil level check and cable inspection
- Interval: 90 days; typical duration 60 min; trade Robotics (L2)
- Steps:
  1. Check oil level on axes 1-3
  2. Inspect cables, SMB cable
  3. Clean cabinet filters

### PM-A-BAT: SMB battery replacement
- Interval: 730 days; typical duration 45 min; trade Robotics (L2)
- Steps:
  1. Replace SMB battery
  2. Verify revolution counters
- Parts/consumables: ABB-SMB-BAT (SMB battery 3.6 V)

### PM-A-OIL: Gearbox oil change (OEM ~10,000 h)
- Interval: 10000 operating hours; typical duration 360 min; trade Robotics (L3)
- Steps:
  1. Drain and refill axes 1-3
  2. Check backlash
  3. Reset service counters
- Parts/consumables: ABB-OIL-SYN (Synthetic gear oil 5 L)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### ABB-20252: Motor ON state: no DC link voltage
- **Severity:** 2  |  **Typical MTTR:** 60-240 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Contactor not closing; Drive unit fault
- **Corrective actions:**
  1. Check DC link and contactor sequence
  2. Replace drive unit
- **Parts likely needed:** ABB-3HAC-DRV (Axis drive unit)

### ABB-38103: Brake failure on axis
- **Severity:** 3  |  **Typical MTTR:** 180-600 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Brake wear; Brake release fault
- **Corrective actions:**
  1. Run brake check
  2. Measure release voltage
  3. Replace brake/motor and recalibrate
- **Parts likely needed:** ABB-MTR-AX2 (Axis 2 motor)
- **Early-warning signature:** channel `motor_current_a` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### ABB-50026: Joint collision (collision detection triggered)
- **Severity:** 2  |  **Typical MTTR:** 15-120 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Fixture misplacement; Payload mismatch; Gearbox wear
- **Corrective actions:**
  1. Check cell for obstructions
  2. Verify load data (LoadIdentify)
  3. Inspect gearbox noise
- **Early-warning signature:** channel `motor_current_a` shows spike before failure.

### ABB-39007: SMB battery low / serial measurement board data at risk
- **Severity:** 2  |  **Typical MTTR:** 30-90 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** SMB backup battery low
- **Corrective actions:**
  1. Replace SMB battery
  2. Verify revolution counters; update if needed
- **Parts likely needed:** ABB-SMB-BAT (SMB battery 3.6 V)
- **Early-warning signature:** channel `battery_voltage_v` shows decay before failure.

### ABB-ENC-CABLE: Intermittent encoder communication errors
- **Severity:** 2  |  **Typical MTTR:** 60-240 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Dress pack cable fatigue; Connector contamination
- **Corrective actions:**
  1. Inspect/replace motor feedback cable
  2. Reseat connectors, apply contact cleaner
- **Parts likely needed:** ABB-CBL-SMB (SMB signal cable)

### ABB-GEAR-NOISE: Abnormal gearbox noise/vibration on axis 3
- **Severity:** 2  |  **Typical MTTR:** 90-480 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Reducer wear; Low lubricant level
- **Corrective actions:**
  1. Check oil level and sample oil (Fe ppm)
  2. Vibration analysis on gearbox
  3. Plan reducer replacement if Fe > 200 ppm
- **Parts likely needed:** ABB-OIL-SYN (Synthetic gear oil 5 L)
- **Early-warning signature:** channel `vibration_mm_s` shows drift up before failure.

## 7. Symptom-to-cause quick guide

- If `motor_current_a` is abnormal, think of: ABB-38103 (brake failure on axis); ABB-50026 (joint collision (collision detection triggered)).
- If `battery_voltage_v` is abnormal, think of: ABB-39007 (sMB battery low / serial measurement board data at risk).
- If `vibration_mm_s` is abnormal, think of: ABB-GEAR-NOISE (abnormal gearbox noise/vibration on axis 3).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| ABB-3HAC-DRV | Axis drive unit | 3,200 |
| ABB-CBL-SMB | SMB signal cable | 780 |
| ABB-MTR-AX2 | Axis 2 motor | 5,200 |
| ABB-OIL-SYN | Synthetic gear oil 5 L | 150 |
| ABB-SMB-BAT | SMB battery 3.6 V | 95 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0114  |  Contract: Standard 8x5 + emergency  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
