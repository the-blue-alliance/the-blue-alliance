"""Joint ranking-point PMF from win, tie, loss and bonus RP probabilities.

A qualification alliance earns RP = win_val * W + tie_val * T + sum_k B_k, where W and T
are the win and tie indicators and B_k are the bonus RP indicators. The events are not
independent. A strong alliance tends to win and to reach the bonus thresholds in the same
match. On DEV, the bonus rate given a win is 0.04 to 0.09 above the forecast probability,
and it is the same amount below given a loss.

Model (a Gaussian copula on the match outcome):

- A latent match-performance variable Z ~ N(0, 1) sets the outcome: loss if Z <= b, tie if
  b < Z <= a, win if Z > a. The thresholds reproduce P(W), P(T) and P(L).
- Each bonus RP has a latent Z_k = rho_k Z + sqrt(1 - rho_k^2) e_k with independent
  e_k ~ N(0, 1). B_k = 1 if Z_k exceeds the threshold that reproduces the forecast q_k.
- Given Z, the bonus RPs are independent. Their mutual dependence comes only through Z.

The marginals W, T, L and B_k stay equal to the forecast probabilities. rho_k is learned
online per season and key by a grid posterior on the observed (outcome, B_k) pairs. The tie
probability is P(T) = c * phi(Phi^-1(p)), which is the density of a continuous margin at 0
times one point. c (the inverse margin scale in points) is learned online per season.

`p` is the model's win probability with ties counted as half a win, so
P(W) = p - P(T)/2 and P(L) = 1 - p - P(T)/2.
"""

from __future__ import annotations

import math
from typing import Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.special import ndtr, ndtri

#: Grid of the copula correlation rho_k. The likelihood is computed on this grid.
RHO_GRID = np.linspace(-0.5, 0.95, 30)
#: Fine grid for the posterior moments. A season has thousands of observations, so the
#: posterior sd (about 0.01 to 0.03) is smaller than the RHO_GRID step (0.05). A cubic
#: spline of the log posterior on RHO_GRID, evaluated here, removes the quantization.
RHO_FINE = np.linspace(-0.5, 0.95, 291)


def rp_values(season: Optional[int]) -> Tuple[int, int]:
    """Return (win RP, tie RP) for a season: (3, 1) from 2025, else (2, 1).

    This is the one season-to-RP-value mapping in hkf. `>= 2025` also covers 2026.
    """
    return (3, 1) if season is not None and season >= 2025 else (2, 1)


def _phi(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


class RPJoint:
    """Online joint RP PMF (see the module docstring).

    Args:
        rho_prior: prior mean of rho_k.
        rho_prior_sd: prior sd of rho_k on the grid.
        tie_c_prior: prior of c in P(T) = c * phi(Phi^-1(p)), used before any season data.
        tie_prior_w: prior weight of c, in units of sum phi(Phi^-1(p)) (about 2.5 matches each).
        nodes: quadrature nodes per outcome region.
        max_tie: upper bound of P(T) as a fraction of 2 * min(p, 1 - p).
    """

    def __init__(
        self,
        rho_prior: float = 0.3,
        rho_prior_sd: float = 0.2,
        tie_c_prior: float = 0.03,
        tie_prior_w: float = 20.0,
        nodes: int = 16,
        max_tie: float = 0.9,
    ) -> None:
        self.rho_prior = float(rho_prior)
        self.rho_prior_sd = float(rho_prior_sd)
        self.tie_c_prior = float(tie_c_prior)
        self.tie_prior_w = float(tie_prior_w)
        self.nodes = int(nodes)
        self.max_tie = float(max_tie)
        self._log_prior = -0.5 * ((RHO_GRID - self.rho_prior) / self.rho_prior_sd) ** 2
        # Pooled tie statistics of past seasons (the prior of the next season).
        self.tie_pool = [0.0, 0.0]  # sum of ties, sum of phi(Phi^-1(p))
        self.tie = [0.0, 0.0]  # the same sums for the current season
        self.start_season()

    # ------------------------------------------------------------------ season state
    def start_season(self) -> None:
        """Start a new season.

        The tie statistics of the finished season move into the pooled prior. The rho
        likelihoods restart from the prior, because the bonus RP rules change every season.
        """
        self.tie_pool[0] += self.tie[0]
        self.tie_pool[1] += self.tie[1]
        self.tie = [0.0, 0.0]
        self.loglik: Dict[str, np.ndarray] = {}  # key -> log likelihood per grid value
        self._rho_cache: Dict[str, float] = {}

    # ------------------------------------------------------------------ parameters
    def tie_c(self) -> float:
        """Current estimate of c in P(T) = c * phi(Phi^-1(p))."""
        c0 = self.tie_c_prior
        if self.tie_pool[1] > 0:
            c0 = (self.tie_pool[0] + self.tie_prior_w * self.tie_c_prior) / (
                self.tie_pool[1] + self.tie_prior_w
            )
        return (self.tie[0] + self.tie_prior_w * c0) / (self.tie[1] + self.tie_prior_w)

    def rho_posterior(self, key: str) -> Tuple[float, float]:
        """Posterior mean and sd of rho for a bonus key in the current season."""
        lp = self._log_prior + self.loglik.get(key, 0.0)
        lf = CubicSpline(RHO_GRID, lp)(RHO_FINE)
        w = np.exp(lf - lf.max())
        w /= w.sum()
        mean = float(w @ RHO_FINE)
        return mean, float(math.sqrt(max(float(w @ (RHO_FINE - mean) ** 2), 0.0)))

    def rho(self, key: str) -> float:
        """Posterior mean of rho for a bonus key in the current season.

        The method does not change state, so a forecast stays read-only. `update_bonus`
        stores the posterior mean of every key it updates. A key without observations
        computes the prior mean on each call.
        """
        r = self._rho_cache.get(key)
        return self.rho_posterior(key)[0] if r is None else r

    def outcome_probs(self, p: float) -> Tuple[float, float, float]:
        """Return (P(W), P(T), P(L)) for a win probability p that counts ties as half a win."""
        p = min(max(float(p), 0.0), 1.0)
        z = float(ndtri(min(max(p, 1e-12), 1.0 - 1e-12)))
        pt = min(self.tie_c() * _phi(z), self.max_tie * 2.0 * min(p, 1.0 - p))
        return p - 0.5 * pt, pt, 1.0 - p - 0.5 * pt

    # ------------------------------------------------------------------ quadrature
    def _regions(
        self, p: float
    ) -> Tuple[Tuple[float, float, float], np.ndarray, np.ndarray]:
        """Nodes z and weights per outcome region (loss, tie, win) in probability space."""
        pw, pt, pl = self.outcome_probs(p)
        edges = (0.0, pl, pl + pt, 1.0)
        m = self.nodes
        frac = (np.arange(m) + 0.5) / m
        zs = np.empty((3, m))
        ws = np.empty((3, m))
        for r in range(3):
            lo, hi = edges[r], edges[r + 1]
            u = np.clip(lo + frac * (hi - lo), 1e-15, 1.0 - 1e-15)
            zs[r] = ndtri(u)
            ws[r] = (hi - lo) / m
        return (pl, pt, pw), zs, ws

    @staticmethod
    def _thresholds(
        q: float, rho: np.ndarray, zs: np.ndarray, ws: np.ndarray
    ) -> np.ndarray:
        """Bonus-latent thresholds per rho that make the quadrature marginal equal q exactly.

        The start value -Phi^-1(q) is exact for the continuous integral. Newton steps remove
        the quadrature error, so the PMF mean equals the forecast mean.
        """
        q = min(max(float(q), 1e-9), 1.0 - 1e-9)
        z, w = zs.ravel(), ws.ravel()
        rho = np.atleast_1d(np.asarray(rho, dtype=float))
        s = np.sqrt(np.maximum(1.0 - rho * rho, 1e-12))
        t = np.full(rho.shape, -float(ndtri(q)))
        for _ in range(4):
            x = (rho[None, :] * z[:, None] - t[None, :]) / s[None, :]
            f = w @ ndtr(x) - q
            df = (
                -(
                    w
                    @ (np.exp(-0.5 * np.minimum(x * x, 1e4)) / math.sqrt(2.0 * math.pi))
                )
                / s
            )
            # Safeguard: skip flat points and bound the step, so t stays finite.
            step = np.where(
                np.abs(df) > 1e-12, f / np.where(np.abs(df) > 1e-12, df, 1.0), 0.0
            )
            t = np.clip(t - np.clip(step, -2.0, 2.0), -40.0, 40.0)
        return t

    def _bonus_given_z(
        self, q: float, rho: float, zs: np.ndarray, ws: np.ndarray
    ) -> np.ndarray:
        """P(B_k = 1 | z) at every node (same shape as zs)."""
        t = float(self._thresholds(q, np.array([rho]), zs, ws)[0])
        s = math.sqrt(max(1.0 - rho * rho, 1e-12))
        return ndtr((rho * zs - t) / s)

    # ------------------------------------------------------------------ forecast
    def pmf(
        self,
        p: float,
        bonus: Mapping[str, float],
        win_val: int,
        tie_val: int = 1,
    ) -> np.ndarray:
        """Return the RP PMF on 0 .. win_val + len(bonus) (index = RP value)."""
        keys = sorted(bonus)
        _, zs, ws = self._regions(p)
        size = int(win_val) + len(keys) + 1
        out = np.zeros(size)
        base = (0, int(tie_val), int(win_val))  # loss, tie, win
        pks = {k: self._bonus_given_z(bonus[k], self.rho(k), zs, ws) for k in keys}
        for r in range(3):
            # Bonus-count distribution at each node: convolve the Bernoulli terms.
            cnt = np.zeros((zs.shape[1], len(keys) + 1))
            cnt[:, 0] = 1.0
            for k in keys:
                pk = pks[k][r]
                cnt[:, 1:] = (
                    cnt[:, 1:] * (1.0 - pk)[:, None] + cnt[:, :-1] * pk[:, None]
                )
                cnt[:, 0] *= 1.0 - pk
            mass = ws[r] @ cnt
            out[base[r] : base[r] + len(keys) + 1] += mass
        out = np.clip(out, 0.0, None)
        return out / out.sum()

    @staticmethod
    def median(pmf: Sequence[float]) -> float:
        """Smallest RP value whose CDF reaches 0.5 (a minimizer of the expected absolute error)."""
        c = np.cumsum(np.asarray(pmf, dtype=float))
        return float(int(np.searchsorted(c, 0.5 - 1e-12)))

    # ------------------------------------------------------------------ learning
    def update_tie(self, p_red: float, is_tie: bool) -> None:
        """Add one match to the tie-rate statistics. Call it once per match, with the pre-match p."""
        p = min(max(float(p_red), 1e-12), 1.0 - 1e-12)
        self.tie[0] += 1.0 if is_tie else 0.0
        self.tie[1] += _phi(float(ndtri(p)))

    def update_bonus(
        self,
        p: float,
        bonus: Mapping[str, float],
        result: str,
        labels: Mapping[str, object],
    ) -> None:
        """Add one alliance observation to the rho likelihoods.

        Args:
            p: the alliance's win probability (ties as half a win), before the match.
            bonus: forecast bonus probabilities, before the match.
            result: "W", "T" or "L" for this alliance.
            labels: realized bonus flags per key.
        """
        r = {"L": 0, "T": 1, "W": 2}[result]
        _, zs, ws = self._regions(p)
        z, w = zs[r], ws[r]
        if w.sum() <= 0:
            return
        s = np.sqrt(np.maximum(1.0 - RHO_GRID**2, 1e-12))
        for k, q in bonus.items():
            y = labels.get(k)
            if y is None:
                continue
            t = self._thresholds(q, RHO_GRID, zs, ws)
            pk = ndtr(
                (RHO_GRID[None, :] * z[:, None] - t[None, :]) / s[None, :]
            )  # nodes x grid
            lk = w @ (pk if y else 1.0 - pk)
            self.loglik[k] = self.loglik.get(k, 0.0) + np.log(
                np.maximum(lk / w.sum(), 1e-300)
            )
            self._rho_cache[k] = self.rho_posterior(k)[0]
