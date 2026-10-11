# Machine Manual: Striko Westofen Dosing furnace 12t holding (Dosing Furnace)

**Document ID:** MAN-DOS  |  **Area:** Giga Casting & Machining (CAS)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** CAS-DOS-01, CAS-DOS-02
- **Manufacturer / model:** Striko Westofen / Dosing furnace 12t holding
- **Description:** Molten-aluminum holding and dosing furnace feeding the Giga Press.
- **Typical cycle time:** 95 s
- **Typical replacement value:** about $620,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Molten metal / die water-leak hazards: see SOP-CAS-02. Hydraulic accumulators store energy: depressurize before opening circuits.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| melt_temp_c | C | 700 | 3 | 725 | 740 |
| furnace_power_kw | kW | 210 | 8 | 260 | 300 |
| vibration_mm_s | mm/s | 1.0 | 0.2 | 3.5 | 6.0 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-DOS-W: Weekly dross removal, channel inspection
- Interval: 7 days; typical duration 90 min; trade Mechanical (L1)

### PM-DOS-Q: Quarterly refractory inspection and thermocouple check
- Interval: 90 days; typical duration 180 min; trade Electrical (L2)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### DOS-TC-DRIFT: Melt thermocouple drift / over-temperature
- **Severity:** 2  |  **Typical MTTR:** 45-180 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Thermocouple sheath degraded
- **Corrective actions:**
  1. Replace thermocouple; verify with immersion probe
- **Parts likely needed:** DOS-TC-SHEATH (Thermocouple with ceramic sheath)
- **Early-warning signature:** channel `melt_temp_c` shows drift up before failure.

### DOS-DOSE-ERR: Dosing quantity deviation
- **Severity:** 2  |  **Typical MTTR:** 60-300 min  |  **Trade:** Mechanical  |  **Code source:** `synthetic`
- **Probable causes:** Pressure sensor drift; Dosing channel buildup
- **Corrective actions:**
  1. Clean dosing channel; recalibrate

### DOS-HEATER: Heating element failure
- **Severity:** 3  |  **Typical MTTR:** 240-1200 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Element aging; Dross attack
- **Corrective actions:**
  1. Replace element; check refractory
- **Parts likely needed:** DOS-HTR-ELEM (Heating element)
- **Early-warning signature:** channel `furnace_power_kw` shows drift up before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

## 7. Symptom-to-cause quick guide

- If `melt_temp_c` is abnormal, think of: DOS-TC-DRIFT (melt thermocouple drift / over-temperature).
- If `furnace_power_kw` is abnormal, think of: DOS-HEATER (heating element failure).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| DOS-HTR-ELEM | Heating element | 1,900 |
| DOS-TC-SHEATH | Thermocouple with ceramic sheath | 340 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0116  |  Contract: Standard  |  Phone response: 4 h  |  On-site: 48 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
