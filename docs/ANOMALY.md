# Anomaly detection

Real, trained detector that runs inside the SimPy engine (`sim/plantsim/anomaly/`). It replaces the scripted alert: the hero alert now fires when the model sees the bearing wear in the telemetry, not at a fixed time.

## Method

1. **Telemetry.** Per machine, per minute: vibration RMS, bearing-defect band, temperature, motor current, load, up fraction. The engine produces it with the same dynamics as the data generator (`sim/plantsim/health.py`).
2. **Load-normalised features** (`features.py`). Each signal is divided by what a healthy machine of that kind gives at the same load (baseline fitted on healthy data only). Temperature is compared with a first-order thermal model (900 s lag of the load, rated rise per machine). Features: vibration ratio, band ratio, temperature residual, current ratio, 30-min vibration and band slopes (5-min smoothing).
3. **Isolation Forest**, trained on healthy shifts only. No fault labels are used for the detector.
4. **Alert rules.** Watch = score above the watch threshold for 10 min; critical = above the critical threshold for 5 min. Thresholds are the lowest on a healthy validation set with zero false alerts. Alerts clear after 20 quiet minutes.
5. **Explanation.** Exact interventional Shapley values over the 6 features (64 coalitions, healthy background of 48 rows). Cross-checked against the `shap` library.
6. **RUL.** Gradient boosting on the wear period, with split-conformal offsets for an 80% interval.

## Held-out results (40 faulty episodes, 16 healthy shifts, never seen in training)

| Metric | Value |
|---|---|
| Window AUROC / average precision | 0.999 / 0.97 |
| Episodes detected before failure | 40 / 40 |
| Median warning before failure | 160 min |
| Median time from wear start to critical alert | 16 min (vibration only 1.05x healthy) |
| Lead over the old rule (vibration > 2x) | 104 min median |
| False alerts, healthy machine-shifts | 0 per 100 |
| False alerts on other machines in faulty shifts | 0 |
| RUL error within 90 min of failure (MAE) | 7 min |
| 80% interval coverage | 0.99 (conservative) |
| Exact Shapley vs `shap` library (Spearman) | 0.95 |

Full numbers: `sim/models/anomaly_report.json`, figure `docs/img/anomaly-report.png`.

In the engine (`detector="all"`, all 10 machines monitored for the shift) the only alert is the real M05 bearing wear (critical at 3.4 h, RUL ~160 min, top contributor bearing-defect band).

## Retrain

```bash
cd sim && .venv/bin/python -m plantsim.anomaly.dataset   # healthy and faulty shifts (seeded)
cd sim && .venv/bin/python -m plantsim.anomaly.train     # writes models/anomaly.joblib + report
```

## Honest limits

- Data is synthetic and the fault signature (vibration, band, temperature, current rise) was injected by our own generator, so these numbers show the method works, not how it will do on a real plant.
- Only one failure mode (bearing wear) exists. Other faults would need their own signatures.
- Slope features in streaming mode skip idle minutes, so they differ slightly from the batch version (tested: levels identical, slopes within 0.01 median).
- Thresholds were tuned on a small healthy validation set (16 shifts); the zero-false-alert result is on a different test set but with few machine-shifts.

## Interfaces

- `GET /anomaly`, `GET /anomaly/{machine}`; LLM tool `get_anomaly_report`.
- WebSocket / `/events` alert messages carry `score`, `contributors[{signal, shap}]`, `rul_s`, `rul_low_s`, `rul_high_s`.
- The twin shows contributors and the RUL range in the alert toast and the live-plant-state row when the engine is connected.
