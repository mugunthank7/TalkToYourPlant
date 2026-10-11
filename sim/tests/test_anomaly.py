"""Anomaly detector: streaming == batch features, exact Shapley, fast scoring == sklearn, no false alerts, catches the hero fault."""
import numpy as np
import pandas as pd
import pytest

from plantsim.anomaly import detector as D
from plantsim.anomaly import features as F
from plantsim.anomaly.shapley import shapley
from plantsim.config import Params
from plantsim.model import PlantSim

pytestmark = pytest.mark.skipif(not D.MODEL_PATH.exists(), reason="train the model first: python -m plantsim.anomaly.train")


def test_fast_scoring_matches_sklearn():
    m = D.load_model()
    X = np.random.default_rng(1).normal([1, 1, 0, 1, 0, 0], [0.1, 0.1, 1, 0.05, 0.3, 0.3], (200, 6))
    assert np.abs(D.score_fn(m)(X) - (-m["iso"].score_samples(X))).max() < 1e-9


def test_shapley_sums_to_score_gap():
    m = D.load_model()
    f = D.score_fn(m)
    bg = m["background"]
    x = np.array([1.4, 1.6, 2.0, 1.1, 0.5, 0.6])
    phi = shapley(f, x, bg)
    assert abs(phi.sum() - (f(x[None])[0] - f(bg).mean())) < 1e-6


def test_streaming_features_match_batch():
    m = D.load_model()
    mon = D.Monitor()
    df = pd.read_parquet(D.MODEL_PATH.parent / "data" / "test_healthy.parquet")
    g = df[(df.machine_id == "M05") & (df.shift_id == df.shift_id.iloc[0])].sort_values("minute").reset_index(drop=True)
    bl = m["baselines"]["M05"]
    batch = F.minute_features(g, bl)
    st = D.MachineState()
    got, want = [], []
    for i, row in g.iterrows():
        x = mon._features(st, "M05", row.to_dict())
        if x is not None and batch.loc[i, F.FEATURES].notna().all():
            got.append(x)
            want.append(batch.loc[i, F.FEATURES].to_numpy(dtype=float))
    got, want = np.array(got), np.array(want)
    assert len(got) > 100
    assert np.allclose(got[:, :4], want[:, :4], atol=1e-6)          # level features are identical
    assert np.median(np.abs(got[:, 4:] - want[:, 4:])) < 0.01      # slopes differ only where idle gaps fall in the past window


def test_no_false_alerts_and_hero_caught():
    sim = PlantSim(Params(detector="all"))
    sim.run()
    machines = {a["machine_id"] for a in sim.alerts}
    assert machines == {"M05"}, f"false alerts on {machines - {'M05'}}"
    crit = [a for a in sim.alerts if a["severity"] == "critical"]
    assert crit and crit[0]["t"] < 5.12 * 3600          # earlier than the 2x-vibration rule
    assert crit[0]["contributors"][0]["signal"] in ("bearing-defect band", "bearing-band trend", "vibration", "vibration trend")
    assert crit[0]["rul_low_s"] <= crit[0]["rul_s"] <= crit[0]["rul_high_s"]
