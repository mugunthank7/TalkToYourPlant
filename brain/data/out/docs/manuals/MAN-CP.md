# Machine Manual: Atlas Copco GA 250 VSD+ (Air Compressor)

**Document ID:** MAN-CP  |  **Area:** Utilities & Facilities (UTL)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** UTL-CP-01, UTL-CP-02, UTL-CP-03, UTL-CP-04
- **Manufacturer / model:** Atlas Copco / GA 250 VSD+
- **Description:** Oil-injected screw compressor providing plant compressed air.
- **Duty:** continuous
- **Typical replacement value:** about $185,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| discharge_temp_c | C | 85 | 2 | 100 | 108 |
| motor_current_a | A | 280 | 10 | 350 | 390 |
| hyd_filter_dp_bar | bar | 0.4 | 0.05 | 0.9 | 1.2 |
| vibration_mm_s | mm/s | 2.0 | 0.3 | 5.0 | 8.0 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-CP-M: Monthly drain, cooler clean, filter dP
- Interval: 30 days; typical duration 60 min; trade Mechanical (L1)

### PM-CP-2K: 2,000 h service: oil, filters
- Interval: 2000 operating hours; typical duration 180 min; trade Mechanical (L2)
- Parts/consumables: CMP-OIL-S (Compressor oil 20 L); CMP-SEP-ELEM (Oil separator element)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### CMP-DISCH-TEMP: Discharge temperature high
- **Severity:** 3  |  **Typical MTTR:** 45-240 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Cooler fouled; Oil level low; Thermostatic valve fault
- **Corrective actions:**
  1. Clean cooler; check oil level
  2. Replace thermostatic valve
- **Parts likely needed:** CMP-OIL-S (Compressor oil 20 L)
- **Early-warning signature:** channel `discharge_temp_c` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### CMP-OIL-SEP: Oil separator differential pressure high
- **Severity:** 2  |  **Typical MTTR:** 60-180 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Separator element loaded
- **Corrective actions:**
  1. Replace separator element and oil filter
- **Parts likely needed:** CMP-SEP-ELEM (Oil separator element)
- **Early-warning signature:** channel `hyd_filter_dp_bar` shows drift up before failure.

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

- If `discharge_temp_c` is abnormal, think of: CMP-DISCH-TEMP (discharge temperature high).
- If `hyd_filter_dp_bar` is abnormal, think of: CMP-OIL-SEP (oil separator differential pressure high).
- If `motor_current_a` is abnormal, think of: CMP-MOTOR-OL (main motor overload trip).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| CMP-DRAIN | Zero-loss condensate drain | 190 |
| CMP-MTR-BRG | Motor bearing kit | 380 |
| CMP-OIL-S | Compressor oil 20 L | 260 |
| CMP-SEP-ELEM | Oil separator element | 420 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0123  |  Contract: Gold  |  Phone response: 4 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
