# Machine Manual: FANUC M-10iD/12 (Cell Stacking Robot)

**Document ID:** MAN-BS  |  **Area:** Battery Pack Assembly (BAT)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** M08, BAT-BS-02, BAT-BS-03, BAT-BS-04
- **Manufacturer / model:** FANUC / M-10iD/12
- **Description:** Robot stacking prismatic cells into modules with compression control.
- **Typical cycle time:** 45 s
- **Typical replacement value:** about $65,000 per unit

## 2. Verified public reference facts

- SRVO-062 BZAL: no backup battery voltage detected at the pulsecoder - mastering data lost, remastering required; SRVO-065 BLAL: low battery voltage warning, data still intact. Typical battery life 1-2 years. (source: https://industrialmonitordirect.com/blogs/knowledgebase/fanuc-srvo-062-bzal-alarm-troubleshooting-resolution)
- Typical battery: A02B-0200-K102 lithium (robot base); clear with RES_PCA then master. (source: https://industrialmonitordirect.com/blogs/knowledgebase/fanuc-srvo-062-bzal-alarm-mastering-recovery-procedure)
- SRVO-050 collision detect, SRVO-007 external emergency stop, SRVO-402 DCS alarm and SRVO-230/231 chain abnormal are among frequently encountered FANUC alarms. (source: https://acieta.com/video-library/service)
- OEM PM guidance quoted by CMMS vendors: grease replenishment for J4-J6 at about 600 hrs; full PM (gearbox oil/grease) about 3,850 hrs or 12 months. (source: https://oxmaint.com/industries/steel-plant/industrial-robotic-arm-maintenance-steel-plants-fanuc-kuka-abb)

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Battery area: HV rules in SOP-SAF-02; thermal event response in SOP-SAF-03; use isolated tools only.
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

### PM-R-W: Weekly robot inspection: leaks, cables, teach pendant, gun tips
- Interval: 250 operating hours; typical duration 25 min; trade Robotics (L1)
- Steps:
  1. Visual inspection of dress pack and cables
  2. Check axis seals for grease/oil seepage
  3. Check tip wear and gun alignment
  4. Test e-stop and gate interlocks
  5. Log findings

### PM-R-M: Monthly grease and mechanical check, filter cleaning
- Interval: 800 operating hours; typical duration 60 min; trade Robotics (L1)
- Steps:
  1. Check controller cabinet fans and filters
  2. Check reducer for abnormal noise
  3. Inspect cables and connectors on J5/J6
  4. Verify weld cap changer

### PM-R-BAT: Backup battery replacement (controller + robot base)
- Interval: 365 days; typical duration 45 min; trade Robotics (L2)
- Steps:
  1. Power ON; replace batteries one at a time
  2. Record date
  3. Confirm no BLAL/BZAL alarm
- Parts/consumables: FAN-A02B-0200-K102 (Lithium backup battery A02B-0200-K102)

### PM-R-GRS: Grease replenishment (J4-J6) per OEM table
- Interval: 600 operating hours; typical duration 90 min; trade Robotics (L2)
- Steps:
  1. Purge grease at drain ports
  2. Apply specified grease volume per axis
  3. Wipe, run-in cycle
- Parts/consumables: ROBO-GREASE-VIGO (Reducer grease 400 g)

### PM-R-ANN: Annual full PM: gearbox oil, brake test, mastering check, backup
- Interval: 3850 operating hours; typical duration 420 min; trade Robotics (L3)
- Steps:
  1. Backup all programs and parameters
  2. Change reducer oil on J1-J3; inspect drained oil for metal
  3. Brake test all axes
  4. Verify mastering
  5. Check cables and replace dress pack if worn
  6. Safety validation (ISO 10218) of gates and safety chain
- Parts/consumables: ROBO-OIL-RV (Reducer oil 4 L)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### SRVO-062: BZAL alarm: pulsecoder backup battery voltage zero, absolute position lost
- **Severity:** 3  |  **Typical MTTR:** 90-300 min  |  **Trade:** Robotics  |  **Code source:** `oem_public`
- **Probable causes:** Encoder backup battery fully discharged; Battery cable disconnected or broken inside base; Controller powered off for a long period with dead battery
- **Corrective actions:**
  1. Replace robot base and controller batteries (A02B-0200-K102 lithium)
  2. Clear alarm with RES_PCA from the pulsecoder screen and cycle power
  3. Re-master the affected axes (zero-position or quick mastering) and verify against witness marks
  4. Validate TCP and run the weld/path accuracy check before returning to production
- **Parts likely needed:** FAN-A02B-0200-K102 (Lithium backup battery A02B-0200-K102)
- **Early-warning signature:** channel `battery_voltage_v` shows decay before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### SRVO-065: BLAL alarm: pulsecoder battery voltage low (data still intact)
- **Severity:** 1  |  **Typical MTTR:** 20-45 min  |  **Trade:** Robotics  |  **Code source:** `oem_public`
- **Probable causes:** Battery approaching end of life (1-2 year typical life); Missed preventive battery replacement
- **Corrective actions:**
  1. Replace batteries within the same shift while power is ON to keep mastering data
  2. Record replacement date on the robot asset tag
- **Parts likely needed:** FAN-A02B-0200-K102 (Lithium backup battery A02B-0200-K102)
- **Early-warning signature:** channel `battery_voltage_v` shows decay before failure.

### SRVO-050: Collision detect alarm
- **Severity:** 2  |  **Typical MTTR:** 15-120 min  |  **Trade:** Robotics  |  **Code source:** `oem_public`
- **Probable causes:** Part or fixture misplaced in the cell; Gun tip stuck to panel; Wrong payload setting; Reducer wear causing disturbance torque rise
- **Corrective actions:**
  1. Back the robot out in T1 using the collision release
  2. Inspect tooling, gun and fixture for damage
  3. Verify payload/armload settings
  4. Check J2/J3 reducer for abnormal noise and disturbance torque
- **Early-warning signature:** channel `motor_current_a` shows spike before failure.

### SRVO-007: External emergency stop
- **Severity:** 2  |  **Typical MTTR:** 5-60 min  |  **Trade:** Robotics  |  **Code source:** `oem_public`
- **Probable causes:** Safety gate or light curtain tripped; E-stop button engaged; Safety relay fault
- **Corrective actions:**
  1. Identify which safety device opened using the cell safety HMI
  2. Reset the device and the safety relay
  3. Verify chain status before resuming
- **Parts likely needed:** SAF-PILZ-PNOZ-S4 (Pilz PNOZ s4 safety relay)

### SRVO-402: DCS (Dual Check Safety) alarm: safe position/speed violation
- **Severity:** 3  |  **Typical MTTR:** 60-240 min  |  **Trade:** Robotics  |  **Code source:** `oem_public`
- **Probable causes:** DCS parameter checksum mismatch after a program change; Robot left safe zone; Mastering offset out of tolerance
- **Corrective actions:**
  1. Review DCS settings against the last approved backup
  2. Re-apply DCS parameters and cycle power
  3. Re-verify mastering; run DCS verification report and obtain controls engineer signoff
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### SRVO-230: Chain 1 (+24V) abnormal
- **Severity:** 2  |  **Typical MTTR:** 30-150 min  |  **Trade:** Robotics  |  **Code source:** `oem_public`
- **Probable causes:** Intermittent safety chain contact; Teach pendant e-stop circuit fault; Loose terminal on EMG board
- **Corrective actions:**
  1. Check the chain status screen for which input is open
  2. Reseat EMG board connectors
  3. Replace faulty pendant cable if intermittent
- **Parts likely needed:** FAN-A05B-2255-C103 (iPendant cable 10 m)

### SRVO-021: SRDY off: servo amplifier not ready
- **Severity:** 2  |  **Typical MTTR:** 60-300 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Amplifier fault latched; Contactor failure; Loss of DC link
- **Corrective actions:**
  1. Check amplifier status LEDs
  2. Inspect main contactor and DC link
  3. Replace servo amplifier if failed
- **Parts likely needed:** FAN-A06B-6290-H208 (Servo amplifier module)
- **Early-warning signature:** channel `motor_temp_c` shows drift up before failure.

### MOTN-023: Motion error: positional deviation exceeds limit on weld path
- **Severity:** 1  |  **Typical MTTR:** 20-90 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Wrist reducer backlash; Tool center point drift after tip change; Fixture clamp not fully engaged
- **Corrective actions:**
  1. Re-teach TCP
  2. Measure backlash on J4-J6
  3. Check fixture clamp sensors

## 7. Symptom-to-cause quick guide

- If `battery_voltage_v` is abnormal, think of: SRVO-062 (bZAL alarm: pulsecoder backup battery voltage zero, absolute position lost); SRVO-065 (bLAL alarm: pulsecoder battery voltage low (data still intact)).
- If `motor_current_a` is abnormal, think of: SRVO-050 (collision detect alarm).
- If `motor_temp_c` is abnormal, think of: SRVO-021 (sRDY off: servo amplifier not ready).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| FAN-A02B-0200-K102 | Lithium backup battery A02B-0200-K102 | 38 |
| FAN-A05B-2255-C103 | iPendant cable 10 m | 480 |
| FAN-A06B-6290-H208 | Servo amplifier module | 2,450 |
| ROBO-GREASE-VIGO | Reducer grease 400 g | 55 |
| ROBO-OIL-RV | Reducer oil 4 L | 140 |
| SAF-PILZ-PNOZ-S4 | Pilz PNOZ s4 safety relay | 210 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0113  |  Contract: Premier 24/7  |  Phone response: 1 h  |  On-site: 12 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
