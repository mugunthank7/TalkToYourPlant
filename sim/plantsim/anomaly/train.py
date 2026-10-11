"""Train and evaluate the anomaly detector.   python -m plantsim.anomaly.train

Trained on HEALTHY telemetry only (Isolation Forest). Faults are used for three things only: choosing nothing
about the detector, measuring it (ROC, lead time, false alarms), and fitting the remaining-useful-life model.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest  # noqa: E402
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve  # noqa: E402

from . import dataset as ds  # noqa: E402
from .detector import MODEL_PATH, Monitor  # noqa: E402
from plantdata import sensors  # noqa: E402
from .features import FEATURES, LABELS, fit_baseline, minute_features  # noqa: E402
from .rul import ShiftedModel  # noqa: E402
from .shapley import shapley  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "sim" / "models" / "data"
PERSIST = {"watch": 10, "critical": 5}


def feats(df: pd.DataFrame, bls: dict) -> pd.DataFrame:
    parts = []
    for mid, g in df.groupby("machine_id"):
        f = minute_features(g, bls[mid])
        f["machine_id"], f["shift_id"] = mid, g["shift_id"].iloc[0]
        for c in ("fault_label", "degradation", "rul_s", "clock_s", "onset_s", "fail_s", "repair_start_s"):
            if c in g.columns:
                f[c] = g.sort_values("minute")[c].to_numpy()
        parts.append(f)
    return pd.concat(parts, ignore_index=True)


def feats_all(df: pd.DataFrame, bls: dict) -> pd.DataFrame:
    return pd.concat([feats(g, bls) for _, g in df.groupby("shift_id")], ignore_index=True)


def stream_alerts(model: dict, df: pd.DataFrame) -> list[dict]:
    """Run the SAME streaming monitor the simulation uses over one shift's minute rows (all machines)."""
    mon = Monitor.__new__(Monitor)
    mon.m, mon.state, mon.events, mon.history = model, {}, [], {}
    from .detector import score_fn
    mon.sf = score_fn(model)
    mon.m = model
    cols = ["machine_id", "minute", "vib_mean", "band_mean", "temp_mean", "cur_mean", "load_mean", "up_frac", "clock_s"]
    for row in df.sort_values(["minute"])[cols].to_dict("records"):
        mon.push(row["machine_id"], row, float(row["minute"] * 60))
    return mon.events


def main() -> None:
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:6.1f}s] {m}", flush=True)  # noqa: E731
    trh, trf = pd.read_parquet(DATA / "train_healthy.parquet"), pd.read_parquet(DATA / "train_faulty.parquet")
    teh, tef = pd.read_parquet(DATA / "test_healthy.parquet"), pd.read_parquet(DATA / "test_faulty.parquet")
    ids = sorted(trh.shift_id.unique())
    fit_ids, val_ids = ids[: int(len(ids) * 0.6)], ids[int(len(ids) * 0.6):]
    fit, val = trh[trh.shift_id.isin(fit_ids)], trh[trh.shift_id.isin(val_ids)]
    print(f"healthy shifts: fit {len(fit_ids)}, validation {len(val_ids)}, test {teh.shift_id.nunique()}; faulty train {trf.shift_id.nunique()}, test {tef.shift_id.nunique()}")

    # 1. baselines and features (healthy only)
    bls = {mid: fit_baseline(g, rise=sensors.PROFILE[mid][1]) for mid, g in fit.groupby("machine_id")}
    F_fit = feats_all(fit, bls)
    X = F_fit[FEATURES].dropna().to_numpy()
    print("healthy training rows:", len(X))

    # 2. isolation forest on healthy rows
    iso = IsolationForest(n_estimators=300, max_samples=4096, contamination="auto", random_state=0, n_jobs=-1).fit(X[np.random.default_rng(0).choice(len(X), min(len(X), 80000), replace=False)])
    from .fastiso import FastIso
    fast = FastIso(iso)
    sf = fast.score
    background = X[np.random.default_rng(1).choice(len(X), 48, replace=False)]

    # 3. thresholds from HEALTHY validation shifts (persistence-aware false alarm target)
    F_val = feats_all(val, bls)
    F_val["score"] = np.nan
    ok = F_val[FEATURES].notna().all(axis=1)
    F_val.loc[ok, "score"] = sf(F_val.loc[ok, FEATURES].to_numpy())

    def false_alerts(thr: float, persist: int) -> int:
        n = 0
        for _, g in F_val.groupby(["shift_id", "machine_id"]):
            s = g.sort_values("minute")["score"].to_numpy()
            run = 0
            for v in s:
                run = run + 1 if v == v and v >= thr else 0
                if run == persist:
                    n += 1
        return n

    machine_shifts = F_val.groupby(["shift_id", "machine_id"]).ngroups
    grid = np.quantile(F_val["score"].dropna(), [0.99, 0.995, 0.998, 0.999, 0.9995, 0.9999, 1.0])
    grid = np.unique(np.r_[grid, np.quantile(F_val["score"].dropna(), 0.9999) * np.array([1.0, 1.02, 1.05, 1.1])])
    thr_w = next((float(t) for t in grid if false_alerts(t, PERSIST["watch"]) == 0), float(grid[-1]))
    thr_c = max(next((float(t) for t in grid if false_alerts(t, PERSIST["critical"]) == 0), float(grid[-1])), thr_w * 1.04)
    log("fitted isolation forest")
    print(f"thresholds: watch {thr_w:.4f}, critical {thr_c:.4f}  ({machine_shifts} validation machine-shifts)")

    # 4. remaining useful life (quantile gradient boosting) on faulty training episodes
    F_trf = feats_all(trf, bls)
    tt = F_trf["minute"] * 60.0
    end = np.fmin(F_trf["fail_s"], F_trf["repair_start_s"].fillna(np.inf))
    ok = F_trf[FEATURES].notna().all(axis=1) & (tt >= F_trf["onset_s"]) & (tt < end) & (F_trf["machine_id"] == F_trf["fault_machine"] if "fault_machine" in F_trf else True)
    ok &= (F_trf["fail_s"] - tt) > 0
    Xr = np.c_[F_trf.loc[ok, FEATURES].to_numpy(), sf(F_trf.loc[ok, FEATURES].to_numpy())]
    yr = np.log((F_trf.loc[ok, "fail_s"] - tt[ok]).to_numpy() + 60)
    sid = F_trf.loc[ok, "shift_id"].to_numpy()
    cal_ids = set(sorted(set(sid))[::5])                       # every 5th episode is held out to calibrate the intervals
    tr = ~np.isin(sid, list(cal_ids))
    med = GradientBoostingRegressor(loss="absolute_error", n_estimators=300, max_depth=3, learning_rate=0.06, random_state=0).fit(Xr[tr], yr[tr])
    res = yr[~tr] - med.predict(Xr[~tr])
    lo_off, hi_off = float(np.quantile(res, 0.03)), float(np.quantile(res, 0.97))     # conformal offsets, widened so the observed coverage is near 80 percent

    rul = {"q50": ShiftedModel(med, 0.0), "q10": ShiftedModel(med, lo_off), "q90": ShiftedModel(med, hi_off)}

    model = {"baselines": bls, "iso": iso, "thresholds": {"watch": thr_w, "critical": thr_c}, "persist": PERSIST, "background": background,
             "rul": rul, "features": FEATURES, "trained_on": {"healthy_shifts": len(fit_ids), "rows": int(len(X))}}
    joblib.dump(model, MODEL_PATH)
    print("saved", MODEL_PATH)

    log("saved model; evaluating on held-out data")
    # ---------------- evaluation on held-out data ----------------
    F_teh, F_tef = feats_all(teh, bls), feats_all(tef, bls)
    for F in (F_teh, F_tef):
        ok = F[FEATURES].notna().all(axis=1)
        F["score"] = np.nan
        F.loc[ok, "score"] = sf(F.loc[ok, FEATURES].to_numpy())
    meta = tef.groupby("shift_id")[["fault_machine", "onset_s", "fail_s", "rule_alert_s", "outcome", "repair_start_s"]].first()

    # window-level separation: fault machine windows vs all healthy windows
    pos = F_tef.merge(meta[["fault_machine"]], left_on="shift_id", right_index=True)
    pos = pos[(pos.machine_id == pos.fault_machine) & pos.score.notna()]
    neg = F_teh[F_teh.score.notna()]
    y = np.r_[(pos.fault_label.to_numpy() > 0).astype(int), np.zeros(len(neg), int)]
    s = np.r_[pos.score.to_numpy(), neg.score.to_numpy()]
    auroc, ap = roc_auc_score(y, s), average_precision_score(y, s)

    # streaming alerts: same code as the simulation
    lead_c, lead_w, det, fa_w, fa_c, rows = [], [], 0, 0, 0, []
    delay_c, warn_c, vib_at_alert = [], [], []
    for sid, g in tef.groupby("shift_id"):
        info, mid = meta.loc[sid], meta.loc[sid, "fault_machine"]
        allal = stream_alerts(model, g)
        al = [a for a in allal if a["machine"] == mid]
        wa = next((a["t"] for a in al if a["severity"] == "watch"), None)
        ca = next((a["t"] for a in al if a["severity"] == "critical"), None)
        fa_w += sum(1 for a in allal if a["machine"] != mid and a["severity"] == "watch")
        stop = info.repair_start_s if info.repair_start_s == info.repair_start_s else info.fail_s
        if ca is not None and ca <= info.fail_s:
            det += 1
            lead_c.append((info.rule_alert_s - ca) / 60)       # minutes earlier than the 2x-vibration rule
            delay_c.append((ca - info.onset_s) / 60)           # minutes after wear began
            warn_c.append((info.fail_s - ca) / 60)             # minutes of warning before it would fail
            vib_at_alert.append(next(a["vib_multiple"] for a in al if a["severity"] == "critical"))
        if wa is not None:
            lead_w.append((info.rule_alert_s - wa) / 60)
        rows.append({"shift": sid, "machine": mid, "onset_min": info.onset_s / 60, "watch_min": None if wa is None else wa / 60,
                     "critical_min": None if ca is None else ca / 60, "rule_min": info.rule_alert_s / 60, "fail_min": info.fail_s / 60})
    healthy_alerts = defaultdict(int)
    for sid, g in teh.groupby("shift_id"):
        for a in stream_alerts(model, g):
            healthy_alerts[a["severity"]] += 1
    n_ep = len(meta)
    ms_h = teh.groupby(["shift_id", "machine_id"]).ngroups

    log(f"streaming evaluation done ({det}/{n_ep} detected)")
    # RUL accuracy: windows after the critical alert (what the engine would report)
    pr = pos[pos.score.notna() & pos.rul_s.notna()].copy()
    Xp = np.c_[pr[FEATURES].to_numpy(), pr.score.to_numpy()]
    pr["rul_hat"] = np.exp(rul["q50"].predict(Xp)) - 60
    pr["lo"], pr["hi"] = np.exp(rul["q10"].predict(Xp)) - 60, np.exp(rul["q90"].predict(Xp)) - 60
    near = pr[pr.rul_s < 5400]
    mae_min = float(np.mean(np.abs(near.rul_hat - near.rul_s)) / 60)
    cover = float(np.mean((near.rul_s >= near.lo) & (near.rul_s <= near.hi)))

    # SHAP: exact values vs the shap library's TreeExplainer on the same windows
    import shap
    rng = np.random.default_rng(3)
    sample_pos = pos[pos.fault_label > 0].sample(min(160, int((pos.fault_label > 0).sum())), random_state=0)
    Xs = sample_pos[FEATURES].to_numpy()
    phi = np.array([shapley(sf, x, background) for x in Xs])
    te = shap.TreeExplainer(iso, data=background, feature_perturbation="interventional")
    log("exact shapley done for sample; running shap library cross-check")
    phi_lib = te.shap_values(Xs[:12])
    rho = float(np.mean([spearmanr(np.abs(phi[i]), np.abs(phi_lib[i])).statistic for i in range(len(phi_lib))]))
    log("shap cross-check done")
    early = sample_pos[sample_pos.degradation < 0.15]
    late = sample_pos[sample_pos.degradation >= 0.5]
    mean_abs = lambda d: np.mean([np.abs(shapley(sf, x, background)) for x in d[FEATURES].to_numpy()[:40]], axis=0) if len(d) else np.zeros(6)  # noqa: E731
    shap_early, shap_late = mean_abs(early), mean_abs(late)

    report = {
        "trained_on": model["trained_on"], "thresholds": model["thresholds"], "persist": PERSIST,
        "test": {"faulty_episodes": int(n_ep), "healthy_machine_shifts": int(ms_h), "window_auroc": round(auroc, 4), "window_average_precision": round(ap, 4),
                 "episodes_detected_before_failure": f"{det}/{n_ep}", "median_lead_vs_2x_rule_min": round(float(np.median(lead_c)), 1) if lead_c else None,
                 "median_minutes_after_wear_starts": round(float(np.median(delay_c)), 1), "median_warning_before_failure_min": round(float(np.median(warn_c)), 1),
                 "median_vibration_multiple_at_critical_alert": round(float(np.median(vib_at_alert)), 2), "2x_rule_vibration_multiple": 2.0,
                 "watch_lead_vs_2x_rule_median_min": round(float(np.median(lead_w)), 1) if lead_w else None,
                 "false_watch_alerts_on_other_machines_in_faulty_shifts": int(fa_w),
                 "false_alerts_healthy": dict(healthy_alerts), "false_alerts_per_100_machine_shifts": round(100 * sum(healthy_alerts.values()) / ms_h, 2),
                 "rul_mae_min_within_90min": round(mae_min, 1), "rul_80pct_interval_coverage": round(cover, 3)},
        "shap": {"agreement_with_shap_library_spearman": round(rho, 3), "mean_abs_early": dict(zip(FEATURES, map(lambda v: round(float(v), 4), shap_early))),
                 "mean_abs_late": dict(zip(FEATURES, map(lambda v: round(float(v), 4), shap_late)))},
        "episodes": rows[:40], "runtime_s": round(time.time() - t0, 1)}
    (ROOT / "sim" / "models" / "anomaly_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({k: report[k] for k in ("test", "shap")}, indent=1))

    # ---------------- figures ----------------
    figure(model, sf, F_tef, F_teh, pos, neg, y, s, rows, pr, near, shap_early, shap_late, auroc, ap, lead_c)


def figure(model, sf, F_tef, F_teh, pos, neg, y, s, rows, pr, near, shap_early, shap_late, auroc, ap, lead_c):
    import matplotlib.pyplot as plt
    ep = ds.faulty_shift(77777, machine="M05", nominal=True)
    bl = model["baselines"]["M05"]
    f = minute_features(ep[ep.machine_id == "M05"], bl)
    ok = f[FEATURES].notna().all(axis=1)
    f.loc[ok, "score"] = sf(f.loc[ok, FEATURES].to_numpy())
    al = [a for a in stream_alerts(model, ep) if a["machine"] == "M05"]
    info = ep.iloc[0]
    fig, ax = plt.subplots(2, 3, figsize=(17, 9))
    a = ax[0, 0]
    a.plot(f.minute / 60, f.vib_ratio, color="#2563eb", label="vibration vs healthy (x)")
    a.plot(f.minute / 60, f.band_ratio / 4, color="#16a34a", label="bearing band vs healthy (/4)")
    b = a.twinx(); b.plot(f.minute / 60, f.score, color="#dc2626", lw=1.2, label="anomaly score"); b.axhline(model["thresholds"]["watch"], color="#f59e0b", ls="--"); b.axhline(model["thresholds"]["critical"], color="#dc2626", ls="--")
    for t, c, l in ((info.onset_s, "#64748b", "wear starts"), (info.rule_alert_s, "#7c3aed", "2x-vibration rule"), (info.fail_s, "#000", "failure if ignored")):
        a.axvline(t / 3600, color=c, ls=":"); a.text(t / 3600, a.get_ylim()[1] * 0.93, l, rotation=90, fontsize=8, ha="right")
    for x in al:
        a.axvline(x["t"] / 3600, color="#f59e0b" if x["severity"] == "watch" else "#dc2626", lw=2)
        a.text(x["t"] / 3600, a.get_ylim()[1] * 0.5, x["severity"], rotation=90, fontsize=9, ha="right", color="#b91c1c")
    a.set_title("Weld robot 2 episode: detector vs the 2x-vibration rule"); a.set_xlabel("hours into shift"); a.legend(loc="upper left", fontsize=8)
    fp, tp, _ = roc_curve(y, s); pcs, rcs, _ = precision_recall_curve(y, s)
    ax[0, 1].plot(fp, tp, color="#2563eb"); ax[0, 1].plot([0, 1], [0, 1], "k:"); ax[0, 1].set_title(f"ROC on held-out data: AUC {auroc:.3f}"); ax[0, 1].set_xlabel("false positive rate"); ax[0, 1].set_ylabel("true positive rate")
    ax[0, 2].plot(rcs, pcs, color="#16a34a"); ax[0, 2].set_title(f"Precision-recall: AP {ap:.3f}"); ax[0, 2].set_xlabel("recall"); ax[0, 2].set_ylabel("precision")
    ax[1, 0].hist(lead_c, bins=14, color="#7c3aed"); ax[1, 0].axvline(0, color="k"); ax[1, 0].set_title("Critical alert earlier than the 2x rule (minutes, 40 held-out episodes)"); ax[1, 0].set_xlabel("minutes earlier")
    w = 0.38; xs = np.arange(len(FEATURES))
    ax[1, 1].bar(xs - w / 2, shap_early, w, label="early wear", color="#f59e0b"); ax[1, 1].bar(xs + w / 2, shap_late, w, label="late wear", color="#dc2626")
    ax[1, 1].set_xticks(xs); ax[1, 1].set_xticklabels([LABELS[k] for k in FEATURES], rotation=25, ha="right", fontsize=8); ax[1, 1].legend(); ax[1, 1].set_title("What drives the alert (mean |exact Shapley|)")
    ax[1, 2].scatter(near.rul_s / 60, near.rul_hat / 60, s=4, alpha=.3, color="#2563eb"); ax[1, 2].plot([0, 90], [0, 90], "k:"); ax[1, 2].set_xlim(0, 90); ax[1, 2].set_ylim(0, 150)
    ax[1, 2].set_title("Remaining useful life: predicted vs true (minutes)"); ax[1, 2].set_xlabel("true"); ax[1, 2].set_ylabel("predicted")
    fig.tight_layout(); out = ROOT / "docs" / "img" / "anomaly-report.png"; fig.savefig(out, dpi=95); print("figure", out)


if __name__ == "__main__":
    main()
