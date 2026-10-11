# Machine Manual: KUKA Omnimove heavy-load AGV (Decking (Marriage) AGV)

**Document ID:** MAN-DK  |  **Area:** General Assembly (GA)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** GA-DK-01, GA-DK-02, GA-DK-03, GA-DK-04
- **Manufacturer / model:** KUKA / Omnimove heavy-load AGV
- **Description:** AGVs carrying battery pack/drive unit and marrying them to the body.
- **Typical cycle time:** 95 s
- **Typical replacement value:** about $480,000 per unit

## 2. Verified public reference facts

- KRC4 maintenance reminders: gearbox oil replacement 10,000-20,000 h or 3-4 years; inline wrist belt inspection 8,000-10,000 h; ~8 L Shell Tivela S150 per primary axis (QUANTEC). (source: https://industrialmonitordirect.com/blogs/knowledgebase/kuka-krc4-maintenance-plans-clearing-inspection-alarms)
- KR QUANTEC PA: MTBF of the whole arm improved to 400,000 hours; oil change every 20,000 operating hours. (source: https://kuka.com/en-gb/company/press/news/2021/10/kr-quantec-pa)
- KR 90/150/180 asset plans list a 20,000-hour / 5-year gear oil change; burn hazard if oil is changed right after the robot stops. (source: https://www.getmaintainx.com/assets/kuka/industrial-robot-kr-180-r2500-extra)

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| battery_soc_pct | % | 70 | 8 | 25 | 15 |
| motor_current_a | A | 35 | 3 | 55 | 70 |
| vibration_mm_s | mm/s | 1.1 | 0.2 | 3.5 | 6.0 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-DK-W: Weekly wheel/contact inspection and scanner clean
- Interval: 7 days; typical duration 45 min; trade Mechanical (L1)

### PM-DK-A: Annual safety scanner validation
- Interval: 365 days; typical duration 120 min; trade Electrical (L2)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### AGV-BAT-LOW: Battery SoC low / charging contact failure
- **Severity:** 1  |  **Typical MTTR:** 15-60 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Charge contact wear; Charger fault
- **Corrective actions:**
  1. Clean/replace charge contacts
  2. Check charger
- **Parts likely needed:** AGV-CONTACT (Charge contact set)
- **Early-warning signature:** channel `battery_soc_pct` shows drift down before failure.

### AGV-LIDAR: Safety laser scanner fault / dirty
- **Severity:** 2  |  **Typical MTTR:** 20-120 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Lens dirty; Scanner misaligned
- **Corrective actions:**
  1. Clean lens; verify protective field
  2. Realign scanner
- **Parts likely needed:** AGV-SCAN-SICK (Safety laser scanner)

### AGV-NAV-LOST: Localization lost
- **Severity:** 2  |  **Typical MTTR:** 10-60 min  |  **Trade:** Controls / PLC  |  **Code source:** `synthetic`
- **Probable causes:** Environment changed; Map outdated; Wheel slip
- **Corrective actions:**
  1. Re-localize; update map layout
  2. Inspect drive wheels

### AGV-DRIVE-WHEEL: Drive wheel wear / motor overload
- **Severity:** 2  |  **Typical MTTR:** 45-180 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Wheel tread wear; Bearing wear
- **Corrective actions:**
  1. Replace drive wheel assembly
- **Parts likely needed:** AGV-WHEEL (Drive wheel assembly)
- **Early-warning signature:** channel `motor_current_a` shows drift up before failure.

## 7. Symptom-to-cause quick guide

- If `battery_soc_pct` is abnormal, think of: AGV-BAT-LOW (battery SoC low / charging contact failure).
- If `motor_current_a` is abnormal, think of: AGV-DRIVE-WHEEL (drive wheel wear / motor overload).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| AGV-CONTACT | Charge contact set | 180 |
| AGV-SCAN-SICK | Safety laser scanner | 2,200 |
| AGV-WHEEL | Drive wheel assembly | 950 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0112  |  Contract: Gold 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
