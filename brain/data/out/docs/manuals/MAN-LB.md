# Machine Manual: TRUMPF TruDisk 6001 brazing cell (Laser Brazing Cell)

**Document ID:** MAN-LB  |  **Area:** Body-in-White (BIW)  |  **Criticality:** B

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** BIW-LB-01, BIW-LB-02
- **Manufacturer / model:** TRUMPF / TruDisk 6001 brazing cell
- **Description:** Laser brazing of roof seams.
- **Typical cycle time:** 70 s
- **Typical replacement value:** about $1,050,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Class 4 laser: only laser-safety trained staff, see SOP-BAT-02.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| laser_power_pct | % | 100 | 0.7 | 94 | 90 |
| coolant_temp_c | C | 22 | 0.5 | 27 | 31 |
| vibration_mm_s | mm/s | 0.6 | 0.1 | 2.0 | 3.5 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-LSR-W: Weekly optics inspection and protective glass check
- Interval: 7 days; typical duration 30 min; trade Process / Quality (L1)

### PM-LSR-Q: Quarterly chiller service and laser power calibration
- Interval: 90 days; typical duration 180 min; trade Process / Quality (L2)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### LSR-PWR-LOW: Laser output power below tolerance (measured vs. commanded)
- **Severity:** 3  |  **Typical MTTR:** 30-240 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Protective glass contaminated; Diode module degradation; Fiber connector contamination
- **Corrective actions:**
  1. Inspect/replace protective glass
  2. Clean fiber end-face
  3. Run power measurement; schedule diode module service
- **Parts likely needed:** LSR-PROT-GLASS (Protective cover glass (box 10))
- **Early-warning signature:** channel `laser_power_pct` shows drift down before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### LSR-CHL-TEMP: Chiller outlet temperature out of range
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Chiller refrigerant low; Filter blocked; Fouled condenser
- **Corrective actions:**
  1. Check chiller setpoint/flow
  2. Clean condenser
  3. Service chiller
- **Parts likely needed:** CHL-FLT-5U (Chiller water filter)
- **Early-warning signature:** channel `coolant_temp_c` shows drift up before failure.

### LSR-SHUTTER: Safety shutter did not confirm open
- **Severity:** 2  |  **Typical MTTR:** 20-90 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Shutter sensor misaligned; Cable fault
- **Corrective actions:**
  1. Check shutter position sensor
  2. Replace cable
- **Parts likely needed:** LSR-SNSR-SHUT (Shutter proximity sensor)

### LSR-SEAM-VIS: Seam tracking lost / quality gate fail
- **Severity:** 2  |  **Typical MTTR:** 20-120 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Optics contamination; Sensor calibration drift; Part positioning error
- **Corrective actions:**
  1. Clean optics, recalibrate seam tracker
  2. Verify fixture locators

## 7. Symptom-to-cause quick guide

- If `laser_power_pct` is abnormal, think of: LSR-PWR-LOW (laser output power below tolerance (measured vs. commanded)).
- If `coolant_temp_c` is abnormal, think of: LSR-CHL-TEMP (chiller outlet temperature out of range).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CHL-FLT-5U | Chiller water filter | 95 |
| LSR-PROT-GLASS | Protective cover glass (box 10) | 180 |
| LSR-SNSR-SHUT | Shutter proximity sensor | 130 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0119  |  Contract: Gold 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 5, L2 backup 15, L3 supervisor 30, L4 engineer 60, L5 vendor 180, L6 plant mgmt 360
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
