# Machine Manual: Carrier 30XF water-cooled chiller (Process Chiller)

**Document ID:** MAN-CH  |  **Area:** Utilities & Facilities (UTL)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** UTL-CH-01, UTL-CH-02
- **Manufacturer / model:** Carrier / 30XF water-cooled chiller
- **Description:** Process cooling water for lasers, weld guns and die cooling.
- **Duty:** continuous
- **Typical replacement value:** about $420,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| coolant_temp_c | C | 20 | 0.5 | 25 | 29 |
| motor_current_a | A | 140 | 6 | 190 | 220 |
| vibration_mm_s | mm/s | 2.0 | 0.3 | 5.0 | 8.0 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-CH-M: Monthly refrigerant, flow and approach temperature check
- Interval: 30 days; typical duration 90 min; trade Mechanical (L2)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### LSR-CHL-TEMP: Chiller outlet temperature out of range
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Hydraulics / Pneumatics  |  **Code source:** `synthetic`
- **Probable causes:** Chiller refrigerant low; Filter blocked; Fouled condenser
- **Corrective actions:**
  1. Check chiller setpoint/flow
  2. Clean condenser
  3. Service chiller
- **Parts likely needed:** CHL-FLT-5U (Chiller water filter)
- **Early-warning signature:** channel `coolant_temp_c` shows drift up before failure.

### CMP-DRYER-DEW: Dryer dew point alarm (> +10 C)
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Dryer refrigerant low; Condensate drain blocked
- **Corrective actions:**
  1. Inspect drain; service dryer
- **Parts likely needed:** CMP-DRAIN (Zero-loss condensate drain)

### CMP-MOTOR-OL: Main motor overload trip
- **Severity:** 3  |  **Typical MTTR:** 90-360 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Bearing failure; Voltage imbalance
- **Corrective actions:**
  1. Check motor insulation and bearing; check supply
- **Parts likely needed:** CMP-MTR-BRG (Motor bearing kit)
- **Early-warning signature:** channel `motor_current_a` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `coolant_temp_c` is abnormal, think of: LSR-CHL-TEMP (chiller outlet temperature out of range).
- If `motor_current_a` is abnormal, think of: CMP-MOTOR-OL (main motor overload trip).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CHL-FLT-5U | Chiller water filter | 95 |
| CMP-DRAIN | Zero-loss condensate drain | 190 |
| CMP-MTR-BRG | Motor bearing kit | 380 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0131  |  Contract: Gold  |  Phone response: 4 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
