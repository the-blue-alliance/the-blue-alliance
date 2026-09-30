"""Smooth learned score-residual shape: an online Gaussian mixture (E3-gmm).

The hkf score PMF is ``mean + sd * T`` on the integers >= 0. By default ``T`` has a CDF from
0.05-sd bins (``sshape``). This module fits a K-component Gaussian mixture to the same data
instead, which removes the bin-edge steps and most of the sampling noise:

    mass = kn * N(0, 1) + (current-season residuals) + kp * (pooled past seasons) / n_pool

on a fine grid (``bw``, default 0.01 sd). The mixture is refit by weighted EM, warm-started,
after every ``refit`` new residuals and at each season start. ``cdf`` is read-only, so
``predict_match`` never changes the state. The shape is centered (shifted to mean 0) so that it
changes only the PMF shape, like the binned shape.
"""

from __future__ import annotations

import numpy as np
from scipy.special import ndtr


class GmmShape:
    def __init__(
        self,
        B: float,
        bw: float,
        K: int,
        kn: float,
        kp: float,
        refit: int,
        roll_iters: int = 40,
        widen: float = 1.0,
        sdscale: float = 1.0,
    ) -> None:
        self.B, self.bw, self.K, self.kn, self.kp, self.refit = B, bw, K, kn, kp, refit
        self.roll_iters = roll_iters
        self.widen, self.sdscale = float(widen), float(sdscale)
        self.nb = int(round(2 * B / bw))
        edges = np.linspace(-B, B, self.nb + 1)
        c = ndtr(edges)
        c[0], c[-1] = 0.0, 1.0
        self.norm = np.diff(c)  # normal prior mass per fine bin
        self.x = -B + bw * (np.arange(self.nb) + 0.5)
        self.cur = np.zeros(self.nb)
        self.cur_n = 0.0
        self.pool = np.zeros(self.nb)
        self.pool_n = 0.0
        self.since = 0
        self.w = np.full(K, 1.0 / K)
        self.mu = np.linspace(-1.0, 1.0, K) if K > 1 else np.zeros(1)
        self.sd = np.ones(K)
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
        self._read_params()

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

    def _read_params(self) -> None:
        """Component parameters for ``cdf`` after the width knobs (fit state is unchanged).

        ``widen`` = c multiplies each component sd by c and pulls the means toward the center so
        that the mixture variance stays the same (a less peaked core, same spread). If c is too
        large for that, the means collapse to the center and the sd is set to keep the variance.
        ``sdscale`` then multiplies every sd by its value (this raises the variance).
        """
        m = self.shift
        vw = float(self.w @ self.sd**2)
        vb = float(self.w @ (self.mu - m) ** 2)
        c = self.widen
        if c != 1.0 and vw > 0:
            c2 = min(c * c, (vw + vb) / vw)
            s = np.sqrt(max((vw + vb - c2 * vw) / vb, 0.0)) if vb > 0 else 1.0
            self.mu_r = m + s * (self.mu - m)
            self.sd_r = np.sqrt(c2) * self.sd
        else:
            self.mu_r, self.sd_r = self.mu.copy(), self.sd.copy()
        self.sd_r = self.sd_r * self.sdscale

    def cdf(self, z: np.ndarray) -> np.ndarray:
        """CDF of the centered mixture at z (read-only)."""
        zz = np.asarray(z, dtype=float)[:, None] + self.shift
        return (
            self.w[None, :] * ndtr((zz - self.mu_r[None, :]) / self.sd_r[None, :])
        ).sum(1)


class BucketGmmShape(GmmShape):
    """GMM shape of one match bucket (E3c), shrunk toward a global shape.

    mass = kg * (global mass) + kp * (bucket pool) / n_pool + (bucket current residuals)

    The global shape must be updated and rolled before the bucket. ``kn`` is unused.
    """

    def __init__(
        self,
        glob: GmmShape,
        kg: float,
        B: float,
        bw: float,
        K: int,
        kp: float,
        refit: int,
        roll_iters: int = 40,
        widen: float = 1.0,
        sdscale: float = 1.0,
    ) -> None:
        self.glob, self.kg = glob, float(kg)
        super().__init__(B, bw, K, 0.0, kp, refit, roll_iters, widen, sdscale)

    def _mass(self) -> np.ndarray:
        m = self.kg * self.glob._mass() + self.cur
        if self.pool_n > 0:
            m = m + self.kp * self.pool / self.pool_n
        return m / m.sum()
