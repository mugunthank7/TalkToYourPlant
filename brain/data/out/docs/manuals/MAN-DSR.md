# Machine Manual: KUKA KR 120 R2700 extra (Die Spray Robot)

**Document ID:** MAN-DSR  |  **Area:** Giga Casting & Machining (CAS)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** CAS-DSR-01, CAS-DSR-02
- **Manufacturer / model:** KUKA / KR 120 R2700 extra
- **Description:** Robot applying die release agent to the Giga Press die between shots.
- **Typical cycle time:** 95 s
- **Typical replacement value:** about $95,000 per unit

## 2. Verified public reference facts

- KRC4 maintenance reminders: gearbox oil replacement 10,000-20,000 h or 3-4 years; inline wrist belt inspection 8,000-10,000 h; ~8 L Shell Tivela S150 per primary axis (QUANTEC). (source: https://industrialmonitordirect.com/blogs/knowledgebase/kuka-krc4-maintenance-plans-clearing-inspection-alarms)
- KR QUANTEC PA: MTBF of the whole arm improved to 400,000 hours; oil change every 20,000 operating hours. (source: https://kuka.com/en-gb/company/press/news/2021/10/kr-quantec-pa)
- KR 90/150/180 asset plans list a 20,000-hour / 5-year gear oil change; burn hazard if oil is changed right after the robot stops. (source: https://www.getmaintainx.com/assets/kuka/industrial-robot-kr-180-r2500-extra)

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

### PM-K-W: Weekly visual check and leak scan
- Interval: 250 operating hours; typical duration 25 min; trade Robotics (L1)
- Steps:
  1. Inspect arm housing for oil leakage at A1-A3 seals (A4-A6 secondary)
  2. Check cables, dress pack
  3. Test e-stop and gate interlocks

### PM-K-WRIST: Inline wrist belt inspection/tension (A5/A6)
- Interval: 8000 operating hours; typical duration 120 min; trade Robotics (L2)
- Steps:
  1. Remove covers
  2. Check belt condition and tension with sonic tension meter
  3. Re-tension or replace
- Parts/consumables: KUKA-BELT-WRIST (Wrist timing belt)

### PM-K-OIL: Gearbox oil change A1-A3 (OEM interval 10,000-20,000 h)
- Interval: 10000 operating hours; typical duration 360 min; trade Robotics (L3)
- Steps:
  1. Warm robot to operating temp then allow to cool slightly (burn risk)
  2. Pull out the oil drain hose, place receptacle, unscrew union nut
  3. Drain, flush if required
  4. Refill with approved ISO VG 150 synthetic oil to level
  5. Reset maintenance counter on SmartPAD
- Parts/consumables: KUKA-OIL-S150-20L (Shell Tivela S150 gear oil 20 L)

### PM-K-CAB: Controller cabinet inspection: filters, fans, batteries
- Interval: 180 days; typical duration 60 min; trade Robotics (L2)
- Steps:
  1. Clean cabinet filter mats
  2. Check fan operation
  3. Check UPS/battery status

### PM-K-ANN: Annual safety check: brake test and safety validation
- Interval: 365 days; typical duration 180 min; trade Robotics (L3)
- Steps:
  1. Brake test all axes
  2. Safety function validation
  3. Backup and archive project

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### KSS-MAINT-OIL: Maintenance reminder: gear oil change due (A1-A3)
- **Severity:** 1  |  **Typical MTTR:** 120-300 min  |  **Trade:** Robotics  |  **Code source:** `oem_public`
- **Probable causes:** Operating hours reached service interval (10,000-20,000 h or 3-4 years depending on model)
- **Corrective actions:**
  1. Schedule gear oil change using the OEM-approved synthetic ISO VG 150 oil (e.g. Shell Tivela S150 in QUANTEC axes)
  2. Perform oil change with robot warm but not hot, drain per OEM procedure
  3. Reset the maintenance counter in the SmartPAD after service
- **Parts likely needed:** KUKA-OIL-S150-20L (Shell Tivela S150 gear oil 20 L)
- **Early-warning signature:** channel `gearbox_temp_c` shows drift up before failure.

### KSS-27008: Brake test failed on axis
- **Severity:** 3  |  **Typical MTTR:** 120-480 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Brake wear (excess braking angle); Brake contamination with lubricant; Brake release voltage low
- **Corrective actions:**
  1. Repeat brake test
  2. Measure brake release voltage at the motor connector
  3. Replace motor with brake if wear exceeds limit; remaster
- **Parts likely needed:** KUKA-MTR-A4 (Axis 4 motor with brake)
- **Early-warning signature:** channel `motor_current_a` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### KSS-SAFE-EMG: Emergency stop active (external)
- **Severity:** 2  |  **Typical MTTR:** 5-45 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Fence door opened; Light curtain interrupted; E-stop pushed
- **Corrective actions:**
  1. Locate device via KRC4 safety interface status
  2. Reset device and acknowledge on SmartPAD

### KSS-RDC-BAT: RDC (resolver digital converter) battery low / mastering data at risk
- **Severity:** 2  |  **Typical MTTR:** 30-90 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** RDC backup battery low
- **Corrective actions:**
  1. Replace RDC battery in the base within the maintenance window
  2. Check mastering with dial gauge or EMD
- **Parts likely needed:** KUKA-RDC-BAT (RDC battery pack)
- **Early-warning signature:** channel `battery_voltage_v` shows decay before failure.

### KSS-OVERTEMP-A2: Axis 2 motor over-temperature warning
- **Severity:** 2  |  **Typical MTTR:** 20-120 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Cooling fins clogged; Heavy duty cycle; Counterbalance system fault
- **Corrective actions:**
  1. Clean motor cooling surfaces
  2. Check duty cycle and path acceleration
  3. Inspect counterbalance pressure
- **Early-warning signature:** channel `motor_temp_c` shows drift up before failure.

### KSS-GEAR-LEAK: Oil leak detected at A1-A3 gearbox seal
- **Severity:** 2  |  **Typical MTTR:** 120-360 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Seal wear; Over-filled gearbox; Vent plug blocked
- **Corrective actions:**
  1. Inspect and photograph leak source
  2. Replace shaft seal; refill to level
  3. Monitor for 5 shifts
- **Parts likely needed:** KUKA-SEAL-A2 (Axis 2 shaft seal kit)
- **Early-warning signature:** channel `gearbox_temp_c` shows drift up before failure.

### KSS-SPOT-STICK: Weld gun tip stick - motion blocked
- **Severity:** 1  |  **Typical MTTR:** 10-40 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Worn tips; Insufficient cooling water flow; Weld current/time out of schedule
- **Corrective actions:**
  1. Break tips free, dress/replace tips
  2. Verify gun cooling flow >= 4 l/min
  3. Check weld schedule
- **Parts likely needed:** WLD-TIP-CAP-16 (Copper cap tip 16 mm (box 50))

## 7. Symptom-to-cause quick guide

- If `gearbox_temp_c` is abnormal, think of: KSS-MAINT-OIL (maintenance reminder: gear oil change due (A1-A3)); KSS-GEAR-LEAK (oil leak detected at A1-A3 gearbox seal).
- If `motor_current_a` is abnormal, think of: KSS-27008 (brake test failed on axis).
- If `battery_voltage_v` is abnormal, think of: KSS-RDC-BAT (rDC (resolver digital converter) battery low / mastering data at risk).
- If `motor_temp_c` is abnormal, think of: KSS-OVERTEMP-A2 (axis 2 motor over-temperature warning).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| KUKA-BELT-WRIST | Wrist timing belt | 220 |
| KUKA-MTR-A4 | Axis 4 motor with brake | 4,900 |
| KUKA-OIL-S150-20L | Shell Tivela S150 gear oil 20 L | 310 |
| KUKA-RDC-BAT | RDC battery pack | 85 |
| KUKA-SEAL-A2 | Axis 2 shaft seal kit | 240 |
| WLD-TIP-CAP-16 | Copper cap tip 16 mm (box 50) | 62 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0112  |  Contract: Gold 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
