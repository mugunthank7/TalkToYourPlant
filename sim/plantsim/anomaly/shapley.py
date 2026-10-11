"""Exact interventional Shapley values for a model with a handful of features (6 here, so 64 subsets).

phi_i is the average marginal effect of feature i on the anomaly score, replacing "absent" features with
values drawn from healthy background data. phi sums to score(x) - mean(score(background)).
"""
from __future__ import annotations

from itertools import product
from math import factorial
from typing import Callable

import numpy as np


def shapley(score_fn: Callable[[np.ndarray], np.ndarray], x: np.ndarray, background: np.ndarray) -> np.ndarray:
    d = len(x)
    masks = np.array(list(product([0, 1], repeat=d)), dtype=bool)               # (2^d, d), True = feature present
    nb = len(background)
    rows = np.where(masks[:, None, :], x[None, None, :], background[None, :, :])  # (2^d, nb, d)
    v = score_fn(rows.reshape(-1, d)).reshape(len(masks), nb).mean(axis=1)       # value of each coalition
    idx = {tuple(m): i for i, m in enumerate(masks)}
    phi = np.zeros(d)
    for i in range(d):
        for m in masks:
            if m[i]:
                continue
            s = int(m.sum())
            w = factorial(s) * factorial(d - s - 1) / factorial(d)
            with_i = m.copy()
            with_i[i] = True
            phi[i] += w * (v[idx[tuple(with_i)]] - v[idx[tuple(m)]])
    return phi
