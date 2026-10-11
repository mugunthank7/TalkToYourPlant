# Machine Manual: Duerr EcoRP E033i (Paint Robot)

**Document ID:** MAN-PR  |  **Area:** Paint Shop (PNT)  |  **Criticality:** A

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## 1. Identification

- **Plant machine IDs:** PNT-PR-01, PNT-PR-02, PNT-PR-03, PNT-PR-04, PNT-PR-05, PNT-PR-06, PNT-PR-07, PNT-PR-08
- **Manufacturer / model:** Duerr / EcoRP E033i
- **Description:** Six/seven-axis painting robot with EcoBell atomizer.
- **Typical cycle time:** 90 s
- **Typical replacement value:** about $150,000 per unit

## 3. Safety summary

- Follow SOP-SAF-01 (LOTO) for all maintenance; the machine energy-source card is at the machine.
- Explosion-protected zone: see SOP-PNT-01 (purge fault is a Level 6 event).
- Robot cell entry only per SOP-SAF-04; T1 mode, enabling switch in hand.

## 4. Operating parameters and condition-monitoring channels

| Channel | Unit | Nominal | Typical sigma | Warn | Alarm |
|---|---|---|---|---|---|
| motor_current_a | A | 9 | 0.8 | 14 | 18 |
| motor_temp_c | C | 46 | 2 | 70 | 82 |
| bell_speed_krpm | krpm | 45 | 0.3 | 42 | 38 |
| vibration_mm_s | mm/s | 1.3 | 0.25 | 4.0 | 6.5 |

See SOP-MNT-05 for actions at warn/alarm and SOP-OPS-02 for run-extension decisions.

## 5. Preventive maintenance schedule

### PM-PR-D: Daily bell cup cleaning and visual check
- Interval: 1 days; typical duration 20 min; trade Robotics (L1)

### PM-PR-M: Monthly hose/cable inspection and turbine check
- Interval: 30 days; typical duration 90 min; trade Robotics (L2)

### PM-PR-A: Annual atomizer turbine service, purge test
- Interval: 365 days; typical duration 240 min; trade Robotics (L3)

## 6. Fault code reference and troubleshooting

Severity: 1 minor, 2 moderate, 3 major, 4 critical (safety or long stop). MTTR = typical repair time range.

### PR-BELL-SPEED: Atomizer (EcoBell) speed deviation
- **Severity:** 3  |  **Typical MTTR:** 60-240 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Turbine bearing wear; Air supply pressure; Contamination
- **Corrective actions:**
  1. Check turbine air, clean bell cup
  2. Replace turbine
- **Parts likely needed:** PR-TURBINE (Atomizer turbine)
- **Early-warning signature:** channel `bell_speed_krpm` shows drift down before failure.
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### PR-COLOR-CHANGE: Color changer valve stuck / contamination
- **Severity:** 2  |  **Typical MTTR:** 30-180 min  |  **Trade:** Robotics  |  **Code source:** `synthetic`
- **Probable causes:** Valve wear; Solvent contamination
- **Corrective actions:**
  1. Flush color changer; replace valve
- **Parts likely needed:** PR-CC-VALVE (Color changer valve)

### PR-EXPL-INTERLOCK: Explosion-protection purge fault (Ex-zone)
- **Severity:** 4  |  **Typical MTTR:** 30-240 min  |  **Trade:** Electrical  |  **Code source:** `synthetic`
- **Probable causes:** Purge air flow low; Pressure sensor drift
- **Corrective actions:**
  1. Do not start; check purge supply and sensor; follow SOP-PNT-01
- **Parts likely needed:** PR-SNSR-PURGE (Purge pressure sensor)
- **Escalation:** page the Maintenance Supervisor at once for severity 3+ faults.

### PR-FILM-DEFECT: Film build out of tolerance (paint thickness)
- **Severity:** 2  |  **Typical MTTR:** 30-150 min  |  **Trade:** Process / Quality  |  **Code source:** `synthetic`
- **Probable causes:** Flow-rate drift; Bell speed; Shaping air
- **Corrective actions:**
  1. Calibrate flow meter; check shaping air

## 7. Symptom-to-cause quick guide

- If `bell_speed_krpm` is abnormal, think of: PR-BELL-SPEED (atomizer (EcoBell) speed deviation).
- If the machine stops with no code: check E-stop chain/safety devices, air/water supply, and PLC/MES communication.
- Repeated faults within 14 days: escalate to the area engineer (see SOP-MNT-01) and review the work order history.

## 8. Spare parts list

| Part no. | Description | Unit cost (USD) |
|---|---|---|
| PR-CC-VALVE | Color changer valve | 650 |
| PR-SNSR-PURGE | Purge pressure sensor | 340 |
| PR-TURBINE | Atomizer turbine | 4,800 |

## 9. Support and escalation

- Vendor emergency line: +1-800-555-0120  |  Contract: Premium 24/7  |  Phone response: 2 h  |  On-site: 24 h
- Internal escalation timers (minutes of downtime): L1 tech 2, L2 backup 8, L3 supervisor 15, L4 engineer 30, L5 vendor 90, L6 plant mgmt 180
- Escalation roles, on-call rota and machine-specific contacts are in the employee/escalation dataset (`escalation_matrix.json`).

## 10. Revision history
- Rev A (2024-02-01): Initial release for start of production.
- Rev B (2025-02-15): Added condition-monitoring thresholds.
- Rev C (2026-01-20): Updated fault tables after first-year failure analysis.
