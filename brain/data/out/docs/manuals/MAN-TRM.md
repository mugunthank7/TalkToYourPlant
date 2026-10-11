# Machine Manual: Schuler Hydraulic trim press 1,200 t (Trim Press)

**Document ID:** MAN-TRM  |  **Area:** Giga Casting & Machining (CAS)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** CAS-TRM-01
- **Manufacturer / model:** Schuler / Hydraulic trim press 1,200 t
- **Description:** Trims gates and flash from the rear underbody casting.
- **Typical cycle time:** 60 s
- **Typical replacement value:** about $1,100,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Molten metal / die water-leak hazards: see SOP-CAS-02. Hydraulic accumulators store energy: depressurize before opening circuits.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| hyd_pressure_bar | bar | 250 | 4 | 225 | 205 |
| hyd_temp_c | C | 44 | 1.5 | 58 | 65 |
| vibration_mm_s | mm/s | 2.0 | 0.3 | 5.0 | 8.0 |

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

### TRM-PRESS-LOW: Hydraulic system pressure below setpoint
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

### TRM-TEMP-HIGH: Hydraulic oil temperature high
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Cooler fouled; Cooling water flow low; Pump internal leakage
- **Corrective actions:**
  1. Clean oil cooler, verify water flow
  2. Check thermostat valve
  3. Trend temperature vs. cycle count
- **Parts likely needed:** HYD-COOLER-PLATE (Plate-type oil cooler cleaning kit)
- **Early-warning signature:** channel `hyd_temp_c` shows drift up before failure.

### TRM-LEAK: Hydraulic oil leak at hose / fitting
- **Severity:** 2  |  **Typical MTTR:** 45-240 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Hose abrasion; Fitting loosened by vibration; Seal failure
- **Corrective actions:**
  1. Isolate and depressurize per LOTO
  2. Replace hose/fitting, torque to spec
  3. Clean up and top up reservoir
- **Parts likely needed:** HYD-HOSE-ASM (High-pressure hose assembly)
- **Early-warning signature:** channel `hyd_level_pct` shows drift down before failure.

### TRM-FILTER-DP: Filter differential pressure high
- **Severity:** 1  |  **Typical MTTR:** 20-60 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Filter loaded with particles
- **Corrective actions:**
  1. Replace pressure and return filters
  2. Sample oil for particle count (ISO 4406)
- **Parts likely needed:** HYD-FLT-10M (10 micron return filter)
- **Early-warning signature:** channel `hyd_filter_dp_bar` shows drift up before failure.

### TRM-VALVE-STICK: Servo/proportional valve sticking - position deviation
- **Severity:** 3  |  **Typical MTTR:** 90-420 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Contaminated oil; Valve spool wear; Amplifier drift
- **Corrective actions:**
  1. Flush and filter oil
  2. Replace valve; run valve calibration
- **Parts likely needed:** HYD-VLV-SERVO (Servo valve)
- **Early-warning signature:** channel `vibration_mm_s` shows spike before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `hyd_pressure_bar` is abnormal, think of: TRM-PRESS-LOW (hydraulic system pressure below setpoint).
- If `hyd_temp_c` is abnormal, think of: TRM-TEMP-HIGH (hydraulic oil temperature high).
- If `hyd_level_pct` is abnormal, think of: TRM-LEAK (hydraulic oil leak at hose / fitting).
- If `hyd_filter_dp_bar` is abnormal, think of: TRM-FILTER-DP (filter differential pressure high).
- If `vibration_mm_s` is abnormal, think of: TRM-VALVE-STICK (servo/proportional valve sticking - position deviation).
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

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0115  |  Contract: Standard  |  Phone response: 4 h  |  On-site: 36 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
