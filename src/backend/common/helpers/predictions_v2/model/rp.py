"""Online Bayesian logistic regression, and the fallback bonus ranking point model.

Each season defines its own bonus RPs, so one small model per (season, key) learns from
zero at the start of each season. The fallback features come from the score filter:

    x = [1, own shared points / sigma, own robot points / sigma, opponent score / sigma]

The update is the assumed-density (Laplace) filter for logistic regression. The forecast
uses the probit approximation to integrate over the weight uncertainty.
"""

import math
from typing import Dict, Mapping, Optional, Sequence

import numpy as np

from backend.common.helpers.predictions_v2.model.state import register_state


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


@register_state
class OnlineLogit:
    """Gaussian posterior over logistic weights, updated one example at a time."""

    __slots__ = ("S", "q", "q_all", "w")

    def __init__(
        self,
        dim: int,
        prior_var: Sequence[float],
        q: float,
        prior_mean: Optional[Sequence[float]] = None,
        q_all: bool = False,
    ) -> None:
        self.w: np.ndarray = (
            np.zeros(dim)
            if prior_mean is None
            else np.asarray(prior_mean, dtype=float).copy()
        )
        self.S: np.ndarray = np.diag(np.asarray(prior_var, dtype=float))
        self.q = q
        self.q_all = q_all

    def prob(self, x: np.ndarray) -> float:
        m = float(self.w @ x)
        v = float(x @ self.S @ x)
        return sigmoid(m / math.sqrt(1.0 + math.pi * v / 8.0))

    def update(self, x: np.ndarray, y: float) -> None:
        if self.q > 0:
            if self.q_all:
                self.S[np.diag_indices_from(self.S)] += self.q
            else:
                self.S[0, 0] += self.q
        m = float(self.w @ x)
        p = sigmoid(m)
        h = max(p * (1.0 - p), 1e-6)
        Sx = self.S @ x
        v = float(x @ Sx)
        self.S -= np.outer(Sx, Sx) * (h / (1.0 + h * v))
        self.w += (self.S @ x) * (y - p)


@register_state
class BonusModel:
    """Per-season bonus RP logistic models keyed by "rp_1" .. "rp_3"."""

    def __init__(self, prior_var: Sequence[float], q: float) -> None:
        self.prior_var = list(prior_var)
        self.q = q
        self.models: Dict[str, OnlineLogit] = {}

    def reset(self) -> None:
        self.models = {}

    def probs(self, keys: Sequence[str], x: np.ndarray) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for k in keys:
            mdl = self.models.get(k)
            out[k] = 0.5 if mdl is None else mdl.prob(x)
        return out

    def update(self, labels: Mapping[str, int], x: np.ndarray) -> None:
        for k, y in labels.items():
            mdl = self.models.get(k)
            if mdl is None:
                mdl = OnlineLogit(len(x), self.prior_var, self.q)
                self.models[k] = mdl
            mdl.update(x, 1.0 if y else 0.0)
