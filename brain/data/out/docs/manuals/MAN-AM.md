# Machine Manual: MiR MiR1350 (Autonomous Mobile Robot)

**Document ID:** MAN-AM  |  **Area:** Intralogistics (LOG)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** M11, LOG-AM-02, LOG-AM-03, LOG-AM-04, LOG-AM-05, LOG-AM-06
- **Manufacturer / model:** MiR / MiR1350
- **Description:** AMR for line-side material delivery.
- **Duty:** continuous
- **Typical replacement value:** about $65,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| battery_soc_pct | % | 65 | 10 | 25 | 15 |
| motor_current_a | A | 12 | 1.2 | 22 | 28 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-AM-W: Weekly wheels, sensors and contacts
- Interval: 7 days; typical duration 30 min; trade Mechanical (L1)

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

- Vendor emergency line: +1-800-555-0133  |  Contract: Standard  |  Phone response: 8 h  |  On-site: 48 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
