# SOP-MNT-05: Condition Monitoring, Oil Analysis and Alert Thresholds

**Area:** ALL  |  **Owner:** Reliability Engineer  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Purpose
Detect developing failures from sensor trends, oil analysis and thermography so work is planned before breakdown.

## Sensors and thresholds
Each machine publishes channels (vibration mm/s RMS, motor current A, motor temperature C, hydraulic pressure bar, oil temperature C, filter differential pressure bar, battery voltage V, laser power %, etc.). Each channel has a **nominal**, **warn** and **alarm** value defined in the machine record. Actions:
- **Warn:** raise a PdM work order, inspect within 5 working days, increase sampling frequency.
- **Alarm:** treat as imminent failure; supervisor decides whether to continue production using SOP-OPS-02 (run-extension decisions).
- Trends crossing 70% of the nominal-to-warn distance for more than 7 days also trigger a PdM work order.

## Oil analysis
- Gearbox and hydraulic oil sampled quarterly (robot gearboxes at annual PM).
- Iron (Fe) > 200 ppm triggers a work order for oil change and internal inspection.
- Hydraulic fluid cleanliness target ISO 4406 18/16/13 for servo valves (17/15/12 for presses with proportional valves); particle count above target triggers filtration/flush.
- Water > 0.1% in hydraulic oil triggers cooler leak check.

## Thermography
Quarterly on switchgear, VFDs, motor terminal boxes and compressor motors. Hot spots > 15 C over reference or > 40 C over ambient raise a P2 work order.

## Anomaly detection
The plant's anomaly detection model (shared with the digital twin) scores sensor windows and attaches SHAP feature contributions to alerts. Engineers review alerts daily; confirmed true positives are logged as PdM work orders and used to retrain the model.

## References
- Internal
