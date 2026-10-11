# Machine Manual: Schuler MSP 2000 servo press (Servo Press)

**Document ID:** MAN-PRS  |  **Area:** Stamping (STP)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** STP-PRS-01, STP-PRS-02, STP-PRS-03
- **Manufacturer / model:** Schuler / MSP 2000 servo press
- **Description:** Servo-driven stamping press for outer and inner body panels.
- **Typical cycle time:** 6 s
- **Key specifications** (synthetic): force_t = 2000
- **Typical replacement value:** about $7,800,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| hyd_pressure_bar | bar | 160 | 3 | 140 | 125 |
| hyd_temp_c | C | 43 | 1.5 | 56 | 63 |
| vibration_mm_s | mm/s | 2.5 | 0.4 | 6.0 | 9.5 |
| motor_current_a | A | 120 | 6 | 175 | 200 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-HYD-D: Daily hydraulic walk-down: level, temperature, leaks
- Interval: 1 days; typical duration 15 min; trade Hydraulics / Pneumatics (L1)
- Steps:
  1. Check oil level and temperature
  2. Walk-down for leaks
  3. Check accumulator pressure gauges

### PM-HYD-M: Monthly filter dP check, breather and cooler inspection
- Interval: 30 days; typical duration 60 min; trade Hydraulics / Pneumatics (L2)
- Steps:
  1. Read filter dP; replace if > limit
  2. Inspect breather
  3. Check oil cooler water flow
- Parts/consumables: HYD-FLT-10M (10 micron return filter)

### PM-HYD-Q: Quarterly oil sample (particle count, water, viscosity) and accumulator pre-charge
- Interval: 90 days; typical duration 90 min; trade Hydraulics / Pneumatics (L2)
- Steps:
  1. Take oil sample
  2. Check accumulator nitrogen pre-charge
  3. Check hose condition

### PM-HYD-A: Annual hydraulic overhaul check: valves, pumps, hoses; die-lock and safety function test
- Interval: 365 days; typical duration 360 min; trade Hydraulics / Pneumatics (L3)
- Steps:
  1. Test pump delivery vs. baseline
  2. Replace hoses beyond date code
  3. Safety function test (guarding, two-hand)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### PRS-PRESS-LOW: Hydraulic system pressure below setpoint
- **Severity:** 3  |  **Typical MTTR:** 60-360 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Pump wear; Internal leakage in valve block; Accumulator pre-charge loss; Clogged suction strainer
- **Corrective actions:**
  1. Check pump delivery and case drain flow
  2. Check accumulator nitrogen pre-charge
  3. Inspect suction strainer
  4. Replace worn pump or valve cartridge
- **Parts likely needed:** HYD-CART-VLV (Proportional valve cartridge); HYD-FLT-10M (10 micron return filter)
- **Early-warning signature:** channel `hyd_pressure_bar` shows drift down before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### PRS-TEMP-HIGH: Hydraulic oil temperature high
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Cooler fouled; Cooling water flow low; Pump internal leakage
- **Corrective actions:**
  1. Clean oil cooler, verify water flow
  2. Check thermostat valve
  3. Trend temperature vs. cycle count
- **Parts likely needed:** HYD-COOLER-PLATE (Plate-type oil cooler cleaning kit)
- **Early-warning signature:** channel `hyd_temp_c` shows drift up before failure.

### PRS-LEAK: Hydraulic oil leak at hose / fitting
- **Severity:** 2  |  **Typical MTTR:** 45-240 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Hose abrasion; Fitting loosened by vibration; Seal failure
- **Corrective actions:**
  1. Isolate and depressurize per LOTO
  2. Replace hose/fitting, torque to spec
  3. Clean up and top up reservoir
- **Parts likely needed:** HYD-HOSE-ASM (High-pressure hose assembly)
- **Early-warning signature:** channel `hyd_level_pct` shows drift down before failure.

### PRS-FILTER-DP: Filter differential pressure high
- **Severity:** 1  |  **Typical MTTR:** 20-60 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Filter loaded with particles
- **Corrective actions:**
  1. Replace pressure and return filters
  2. Sample oil for particle count (ISO 4406)
- **Parts likely needed:** HYD-FLT-10M (10 micron return filter)
- **Early-warning signature:** channel `hyd_filter_dp_bar` shows drift up before failure.

### PRS-VALVE-STICK: Servo/proportional valve sticking - position deviation
- **Severity:** 3  |  **Typical MTTR:** 90-420 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Contaminated oil; Valve spool wear; Amplifier drift
- **Corrective actions:**
  1. Flush and filter oil
  2. Replace valve; run valve calibration
- **Parts likely needed:** HYD-VLV-SERVO (Servo valve)
- **Early-warning signature:** channel `vibration_mm_s` shows spike before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### PRS-DIE-CUSH: Die cushion pressure loss
- **Severity:** 2  |  **Typical MTTR:** 90-360 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Cushion cylinder seal leak; Valve fault
- **Corrective actions:**
  1. Replace seal kit; recalibrate cushion
- **Parts likely needed:** PRS-SEAL-CUSH (Cushion cylinder seal kit)

### PRS-CLUTCH: Servo drive overload / main motor overtemperature
- **Severity:** 3  |  **Typical MTTR:** 120-600 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Duty cycle; Cooling fault; Bearing wear
- **Corrective actions:**
  1. Check cooling; check motor current profile
- **Parts likely needed:** PRS-MTR-BRG (Main drive motor bearing set)
- **Early-warning signature:** channel `motor_temp_c` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### PRS-DOUBLE-BLANK: Double blank detected
- **Severity:** 2  |  **Typical MTTR:** 10-60 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Sensor sensitivity; Blank destacker malfunction
- **Corrective actions:**
  1. Clear blank; check destacker magnets & sensors

### PRS-TRANSFER: Transfer bar misfeed
- **Severity:** 2  |  **Typical MTTR:** 20-150 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Finger wear; Servo sync error
- **Corrective actions:**
  1. Inspect transfer fingers; resync servo
- **Parts likely needed:** PRS-FINGER-SET (Transfer finger set)

## 7. Symptom-to-cause quick guide

- If `hyd_pressure_bar` is abnormal, think of: PRS-PRESS-LOW (hydraulic system pressure below setpoint).
- If `hyd_temp_c` is abnormal, think of: PRS-TEMP-HIGH (hydraulic oil temperature high).
- If `hyd_level_pct` is abnormal, think of: PRS-LEAK (hydraulic oil leak at hose / fitting).
- If `hyd_filter_dp_bar` is abnormal, think of: PRS-FILTER-DP (filter differential pressure high).
- If `vibration_mm_s` is abnormal, think of: PRS-VALVE-STICK (servo/proportional valve sticking - position deviation).
- If `motor_temp_c` is abnormal, think of: PRS-CLUTCH (servo drive overload / main motor overtemperature).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| HYD-CART-VLV | Proportional valve cartridge | 1,850 |
| HYD-COOLER-PLATE | Plate-type oil cooler cleaning kit | 220 |
| HYD-FLT-10M | 10 micron return filter | 140 |
| HYD-HOSE-ASM | High-pressure hose assembly | 420 |
| HYD-VLV-SERVO | Servo valve | 4,100 |
| PRS-FINGER-SET | Transfer finger set | 540 |
| PRS-MTR-BRG | Main drive motor bearing set | 1,900 |
| PRS-SEAL-CUSH | Cushion cylinder seal kit | 720 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0115  |  Contract: Standard  |  Phone response: 4 h  |  On-site: 36 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
