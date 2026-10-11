# Machine Manual: IDRA GIGAPRESS NEO 6100 (Giga Press)

**Document ID:** MAN-GP  |  **Area:** Giga Casting & Machining (CAS)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** CAS-GP-01, M01
- **Manufacturer / model:** IDRA / GIGAPRESS NEO 6100
- **Description:** High-pressure aluminum die casting machine, 6,100 t class (60,000 kN clamping force), die height 2,400 mm, ~430 t, 20.4 x 7.4 x 6.3 m. Produces the single-piece rear underbody casting.
- **Typical cycle time:** 95 s
- **Key specifications** (oem_public): clamping_force_kN = 60000, weight_t = 430
- **Typical replacement value:** about $9,500,000 per unit

## 2. Verified public reference facts

- IDRA publishes the GIGAPRESS NEO 6100 at 60,000 kN clamping force, 2,400 mm die height, ~430 t weight and 20.4 x 7.4 x 6.3 m footprint. (source: https://idragroup.com/sites/default/files/download/gigapress-catalogue-en_0.pdf)
- Features: DCP hydraulic system with integrated high-flow manifold blocks, Inject Computer 3.x machine management, cell controller integration, easy-maintenance all-in-one manifolds to minimise fluid loss. (source: https://idragroup.com/sites/default/files/download/gigapress-catalogue-en_0.pdf)
- A 6,000 t Giga Press achieves fill times around 120 milliseconds; platens were redesigned and cores moved externally to improve dimensional accuracy. (source: https://leandesign.com/?p=2932)
- IDRA NEO machines use Block-Control tie-bar monitoring with automatic clamping-force adjustment, automatic toggle lubrication and a servo-driven guarding system (per NEO 1000 listing). (source: https://www.werktuigen.com/idra-neo+1000/wt-223-58307)

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Molten metal / die water-leak hazards: see SOP-CAS-02. Hydraulic accumulators store energy: depressurize before opening circuits.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| hyd_pressure_bar | bar | 280 | 4 | 255 | 235 |
| hyd_temp_c | C | 46 | 1.5 | 58 | 65 |
| hyd_filter_dp_bar | bar | 1.2 | 0.2 | 3.0 | 4.0 |
| vibration_mm_s | mm/s | 2.1 | 0.3 | 5.0 | 8.0 |
| hyd_level_pct | % | 92 | 1 | 80 | 70 |

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

### PM-GP-TOGGLE: Toggle linkage lubrication check and tie-bar calibration
- Interval: 30 days; typical duration 120 min; trade Mechanical (L2)
- Steps:
  1. Check automatic toggle lubrication levels
  2. Run tie-bar calibration

### PM-GP-PLUNGER: Shot sleeve and plunger tip inspection
- Interval: 400 operating hours; typical duration 180 min; trade Mechanical (L2)
- Steps:
  1. Inspect plunger tip wear
  2. Measure sleeve ID
  3. Replace per limits
- Parts/consumables: GP-PLUNGER-TIP (Plunger tip)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### GP-PRESS-LOW: Hydraulic system pressure below setpoint
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

### GP-TEMP-HIGH: Hydraulic oil temperature high
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Cooler fouled; Cooling water flow low; Pump internal leakage
- **Corrective actions:**
  1. Clean oil cooler, verify water flow
  2. Check thermostat valve
  3. Trend temperature vs. cycle count
- **Parts likely needed:** HYD-COOLER-PLATE (Plate-type oil cooler cleaning kit)
- **Early-warning signature:** channel `hyd_temp_c` shows drift up before failure.

### GP-LEAK: Hydraulic oil leak at hose / fitting
- **Severity:** 2  |  **Typical MTTR:** 45-240 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Hose abrasion; Fitting loosened by vibration; Seal failure
- **Corrective actions:**
  1. Isolate and depressurize per LOTO
  2. Replace hose/fitting, torque to spec
  3. Clean up and top up reservoir
- **Parts likely needed:** HYD-HOSE-ASM (High-pressure hose assembly)
- **Early-warning signature:** channel `hyd_level_pct` shows drift down before failure.

### GP-FILTER-DP: Filter differential pressure high
- **Severity:** 1  |  **Typical MTTR:** 20-60 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Filter loaded with particles
- **Corrective actions:**
  1. Replace pressure and return filters
  2. Sample oil for particle count (ISO 4406)
- **Parts likely needed:** HYD-FLT-10M (10 micron return filter)
- **Early-warning signature:** channel `hyd_filter_dp_bar` shows drift up before failure.

### GP-VALVE-STICK: Servo/proportional valve sticking - position deviation
- **Severity:** 3  |  **Typical MTTR:** 90-420 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Contaminated oil; Valve spool wear; Amplifier drift
- **Corrective actions:**
  1. Flush and filter oil
  2. Replace valve; run valve calibration
- **Parts likely needed:** HYD-VLV-SERVO (Servo valve)
- **Early-warning signature:** channel `vibration_mm_s` shows spike before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### GP-TIEBAR: Tie-bar load imbalance: clamping force deviation across 4 tie bars
- **Severity:** 3  |  **Typical MTTR:** 90-360 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Die thermal growth; Toggle lubrication lack; Sensor drift
- **Corrective actions:**
  1. Run Block-Control tie-bar calibration
  2. Check automatic toggle lubrication
  3. Re-level die
- **Parts likely needed:** GP-TIEBAR-SNSR (Tie-bar strain sensor)
- **Early-warning signature:** channel `vibration_mm_s` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### GP-SHOT-SLOW: Shot speed profile deviation / fill time out of window (~120 ms target)
- **Severity:** 3  |  **Typical MTTR:** 120-480 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Accumulator pre-charge low; Shot sleeve wear; Valve response degraded
- **Corrective actions:**
  1. Check accumulator pre-charge
  2. Inspect shot sleeve and plunger tip
  3. Calibrate injection valve
- **Parts likely needed:** GP-PLUNGER-TIP (Plunger tip)
- **Early-warning signature:** channel `hyd_pressure_bar` shows drift down before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### GP-DIE-LEAK: Die cooling circuit water leak into die cavity
- **Severity:** 4  |  **Typical MTTR:** 240-1200 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Cracked cooling insert; O-ring failure
- **Corrective actions:**
  1. Stop cycle and secure die; pull die per SOP-CAS-02
  2. Pressure test circuits; replace insert
- **Parts likely needed:** GP-ORING-KIT (Die cooling O-ring kit)
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### GP-GUARD-SERVO: Servo guard door fault / interlock
- **Severity:** 2  |  **Typical MTTR:** 20-120 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Guard sensor misaligned; Servo drive fault
- **Corrective actions:**
  1. Realign guard sensor; check servo drive
- **Parts likely needed:** GP-SNSR-GUARD (Guard safety sensor)

## 7. Symptom-to-cause quick guide

- If `hyd_pressure_bar` is abnormal, think of: GP-PRESS-LOW (hydraulic system pressure below setpoint); GP-SHOT-SLOW (shot speed profile deviation / fill time out of window (~120 ms target)).
- If `hyd_temp_c` is abnormal, think of: GP-TEMP-HIGH (hydraulic oil temperature high).
- If `hyd_level_pct` is abnormal, think of: GP-LEAK (hydraulic oil leak at hose / fitting).
- If `hyd_filter_dp_bar` is abnormal, think of: GP-FILTER-DP (filter differential pressure high).
- If `vibration_mm_s` is abnormal, think of: GP-VALVE-STICK (servo/proportional valve sticking - position deviation); GP-TIEBAR (tie-bar load imbalance: clamping force deviation across 4 tie bars).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| GP-ORING-KIT | Die cooling O-ring kit | 140 |
| GP-PLUNGER-TIP | Plunger tip | 2,800 |
| GP-SNSR-GUARD | Guard safety sensor | 260 |
| GP-TIEBAR-SNSR | Tie-bar strain sensor | 1,900 |
| HYD-CART-VLV | Proportional valve cartridge | 1,850 |
| HYD-COOLER-PLATE | Plate-type oil cooler cleaning kit | 220 |
| HYD-FLT-10M | 10 micron return filter | 140 |
| HYD-HOSE-ASM | High-pressure hose assembly | 420 |
| HYD-VLV-SERVO | Servo valve | 4,100 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0111  |  Contract: Premium 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
