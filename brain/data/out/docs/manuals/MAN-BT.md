# Machine Manual: Desoutter 4-spindle synchronous fastening (20 Nm) (Pack Fastening Station)

**Document ID:** MAN-BT  |  **Area:** Battery Pack Assembly (BAT)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** M09, BAT-BT-02, BAT-BT-03, BAT-BT-04
- **Manufacturer / model:** Desoutter / 4-spindle synchronous fastening (20 Nm)
- **Description:** Synchronous 4-spindle fastening of pack to carrier at up to 20 Nm using galvanically isolated chucks (HV safety).
- **Typical cycle time:** 40 s
- **Key specifications** (oem_public): max_torque_Nm = 20, spindles = 4
- **Typical replacement value:** about $240,000 per unit

## 2. Verified public reference facts

- Synchronous four-spindle fastening up to 20 Nm; galvanically isolated chucks protect workers near 400-800 V packs; a nominal 800 V pack contains about 198 cells in series (610-835 V). (source: https://digitaledition.assemblymag.com/may-2023/screwdriving-battery-packs/)

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Battery area: HV rules in SOP-SAF-02; thermal event response in SOP-SAF-03; use isolated tools only.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| torque_nm | Nm | 18.0 | 0.35 | 16.5 | 15.0 |
| motor_temp_c | C | 40 | 2 | 62 | 75 |
| motor_current_a | A | 6.0 | 0.4 | 9.5 | 12 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-TQ-D: Daily torque verification with test joint
- Interval: 1 days; typical duration 10 min; trade Process / Quality (L1)

### PM-TQ-A: Annual transducer calibration (cert)
- Interval: 365 days; typical duration 120 min; trade Process / Quality (L2)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### TQ-NOK: Tightening result NOK: torque out of window
- **Severity:** 2  |  **Typical MTTR:** 10-60 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Cross-threaded fastener; Tool transducer drift; Socket wear; Joint friction variation (bolt batch)
- **Corrective actions:**
  1. Inspect joint; do NOT re-tighten without quality approval
  2. Run calibration check on the tool
  3. Replace socket if worn
  4. Quarantine suspect fastener lot if repeating
- **Parts likely needed:** TQ-SOCKET-13 (13 mm impact-grade socket)
- **Early-warning signature:** channel `torque_nm` shows drift down before failure.

### TQ-CAL-DUE: Transducer calibration overdue
- **Severity:** 1  |  **Typical MTTR:** 30-120 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Calibration interval exceeded (12 months or 500k cycles)
- **Corrective actions:**
  1. Pull tool; send for calibration; swap with certified spare

### TQ-CBL-FAULT: Tool cable / communication fault
- **Severity:** 1  |  **Typical MTTR:** 15-60 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Flex fatigue in tool cable
- **Corrective actions:**
  1. Replace tool cable; verify controller link
- **Parts likely needed:** TQ-CBL-5M (Tool cable 5 m)

### TQ-MOTOR-TEMP: Tool motor temperature high
- **Severity:** 2  |  **Typical MTTR:** 30-120 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Duty cycle too high; Gear head worn
- **Corrective actions:**
  1. Allow cooldown; check gear head grease
  2. Replace gear head
- **Parts likely needed:** TQ-GEARHEAD (Gear head assembly)
- **Early-warning signature:** channel `motor_temp_c` shows drift up before failure.

### TQ-BATCH-MISS: Fastener count / batch incomplete (missed bolt)
- **Severity:** 3  |  **Typical MTTR:** 20-90 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Operator skipped bolt; Sensor missed pallet position
- **Corrective actions:**
  1. Quarantine vehicle for re-inspection
  2. Review station poka-yoke sensor
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `torque_nm` is abnormal, think of: TQ-NOK (tightening result NOK: torque out of window).
- If `motor_temp_c` is abnormal, think of: TQ-MOTOR-TEMP (tool motor temperature high).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| TQ-CBL-5M | Tool cable 5 m | 210 |
| TQ-GEARHEAD | Gear head assembly | 760 |
| TQ-SOCKET-13 | 13 mm impact-grade socket | 28 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0122  |  Contract: Standard  |  Phone response: 8 h  |  On-site: 48 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
