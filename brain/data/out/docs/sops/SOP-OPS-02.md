# SOP-OPS-02: Run-Extension and Run-to-Failure Risk Decision (e.g. 'Keep running 2 more hours?')

**Area:** ALL  |  **Owner:** Maintenance Manager  |  **Revision:** B  |  **Effective:** 2025-06-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Purpose
Provide a consistent, risk-based way to decide whether a machine showing warning signs may keep producing until a planned stop, a shift end, or a defined time extension.

## Inputs to the decision
1. Machine criticality (A/B/C) and buffer status (how many minutes of downstream stock exist).
2. Sensor channels vs thresholds: nominal / warn / alarm, trend slope (rate of change per hour), and SHAP-contributing features from the anomaly alert.
3. Fault history: same fault code in the last 14/90 days; recent PdM work orders; days since last PM.
4. Safety potential: could the failure create a hazard (HV, molten metal, Ex-zone, hydraulic burst, crane load)?
5. Consequence: estimated downtime if it fails (MTTR for the fault code from the machine manual), parts availability, lost vehicles per hour.

## Rules
- **Safety-critical channels at warn or worse:** never extend. Stop at the earliest safe point and notify L3/L4.
- **Any channel at alarm:** no extension unless the Maintenance Manager approves in writing with a mitigation (reduced speed, extra monitoring every 15 min, tech on standby).
- **Channel at warn, trend flat (< 2% change per hour):** extension up to 2 hours allowed with supervisor approval; technician inspects at the next break; re-evaluate every 30 minutes.
- **Channel at warn, trend rising (> 2% per hour or accelerating):** extension limited to the time needed to complete the current batch or reach a buffer-protected stop (max 30-60 min); schedule repair immediately.
- **Between 70% and 100% of nominal-to-warn distance:** extension allowed to the end of shift; raise PdM work order; add watch to handover.
- **Repeat failure (same fault within 14 days):** treat as warn at minimum; engineer must approve.
- **Criticality-A machine with no spare for a high-MTTR part:** do not run beyond the planned window unless production loss from stopping exceeds the expected loss from a failure (expected loss = probability of failure x MTTR x loss/hour). Document the calculation.

## Documentation
Record the decision, approver, time limit, mitigations and monitoring in the work order and shift handover. After the extension, close the loop: confirm outcome and update the PdM/anomaly model feedback.

## References
- Internal
