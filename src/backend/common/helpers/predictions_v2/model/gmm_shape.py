"""Learned shape of the score residual: an online Gaussian mixture.

The score PMF is ``mean + sd * T`` on the integers >= 0. ``T`` is a K-component Gaussian
mixture fit by weighted EM to

    mass = kn * N(0, 1) + (current-season residuals) + kp * (pooled past seasons) / n_pool

on a fine grid of width ``GRID_W``. The mixture is refit, warm-started, after every
``REFIT_EVERY`` new residuals and at each season start. ``cdf`` is read-only. The shape is centered (shifted
to mean 0), so it changes only the PMF shape.
"""

import numpy as np
from scipy.special import ndtr

from backend.common.helpers.predictions_v2.model.state import register_state

GRID_W = 0.01  # width (sd units) of the residual count grid
REFIT_EVERY = 25  # new residuals between warm-started refits (10 EM iterations each)
ROLL_ITERS = 2000  # EM iterations of the season-start refit (converged)


@register_state
class GmmShape:
    def __init__(self, B: float, K: int, kn: float, kp: float, sdscale: float) -> None:
        bw = GRID_W
        self.B, self.bw, self.K, self.kn, self.kp = B, bw, K, kn, kp
        self.refit = REFIT_EVERY
        self.roll_iters = ROLL_ITERS
        self.sdscale = float(sdscale)
        self.nb = int(round(2 * B / bw))
        edges = np.linspace(-B, B, self.nb + 1)
        c = ndtr(edges)
        c[0], c[-1] = 0.0, 1.0
        self.norm: np.ndarray = np.diff(c)  # normal prior mass per fine bin
        self.x: np.ndarray = np.asarray(-B + bw * (np.arange(self.nb) + 0.5))
        self.cur: np.ndarray = np.zeros(self.nb)
        self.cur_n = 0.0
        self.pool: np.ndarray = np.zeros(self.nb)
        self.pool_n = 0.0
        self.since = 0
        self.w: np.ndarray = np.full(K, 1.0 / K)
        self.mu: np.ndarray = np.linspace(-1.0, 1.0, K) if K > 1 else np.zeros(1)
        self.sd: np.ndarray = np.ones(K)
        self.shift = 0.0
        self.mu_r: np.ndarray = self.mu.copy()
        self.sd_r: np.ndarray = self.sd.copy()
        self._fit(200)

    def _mass(self) -> np.ndarray:
        m = self.kn * self.norm + self.cur
        if self.pool_n > 0:
            m = m + self.kp * self.pool / self.pool_n
        return m / m.sum()

    def _fit(self, iters: int) -> None:
        x, m = self.x, self._mass()
        sd_floor = float(np.sqrt(0.01**2 + self.bw**2 / 12))
        for _ in range(iters):
            dens = self.w[:, None] * np.exp(
                -0.5 * ((x[None, :] - self.mu[:, None]) / self.sd[:, None]) ** 2
            )
            dens /= self.sd[:, None]
            r = dens / np.maximum(dens.sum(0, keepdims=True), 1e-300)
            rm = r * m[None, :]
            nk = rm.sum(1) + 1e-12
            self.w = nk / nk.sum()
            self.mu = (rm @ x) / nk
            var = (rm * (x[None, :] - self.mu[:, None]) ** 2).sum(1) / nk
            self.sd = np.sqrt(np.maximum(var, sd_floor**2))
        self.shift = float(self.w @ self.mu)
        self.since = 0
        self.mu_r, self.sd_r = self.mu.copy(), self.sd.copy() * self.sdscale

    def add(self, t: float) -> None:
        """Add one standardized residual. Refit after ``refit`` new residuals."""
        B = self.B
        i = int((min(max(t, -B + 1e-9), B - 1e-9) + B) / self.bw)
        self.cur[min(max(i, 0), self.nb - 1)] += 1.0
        self.cur_n += 1.0
        self.since += 1
        if self.since >= self.refit:
            self._fit(10)

    def roll(self) -> None:
        """Season start: pool the finished season, clear the current counts, refit."""
        if self.cur_n > 0:
            self.pool += self.cur
            self.pool_n += self.cur_n
        self.cur = np.zeros(self.nb)
        self.cur_n = 0.0
        self._fit(self.roll_iters)

    def cdf(self, z: np.ndarray) -> np.ndarray:
        """CDF of the centered mixture at z. Read-only."""
        zz = np.asarray(z, dtype=float)[:, None] + self.shift
        return (
            self.w[None, :] * ndtr((zz - self.mu_r[None, :]) / self.sd_r[None, :])
        ).sum(1)


@register_state
class BucketGmmShape(GmmShape):
    """Shape of one match bucket, shrunk toward the global shape:

    mass = kg * (global mass) + kp * (bucket pool) / n_pool + (bucket current residuals)

    The global shape must be updated and rolled before the bucket.
    """

    def __init__(
        self,
        glob: GmmShape,
        kg: float,
        B: float,
        K: int,
        kp: float,
        sdscale: float,
    ) -> None:
        self.glob = glob
        self.kg = float(kg)
        super().__init__(B, K, 0.0, kp, sdscale)

    def _mass(self) -> np.ndarray:
        m = self.kg * self.glob._mass() + self.cur
        if self.pool_n > 0:
            m = m + self.kp * self.pool / self.pool_n
        return m / m.sum()
