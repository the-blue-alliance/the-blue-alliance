"""Score structure: the rulebook score components shape the score PMF.

Component model (``ComponentModel``): per score component of the season (see
``rulebook.SCORE_COMPONENTS``), a count histogram per bin of the team strength ratio (team
component rate over the season mean). A shared latent alliance factor (Gauss-Hermite nodes,
loading beta chosen so that the PMF sd matches the base sd) couples the components. The
alliance PMF is the FFT convolution of the component PMFs, tilted so that its mean equals
the base mean.

Score PMF arms (``ScoreStructure``):

* base: the base PMF (no structure).
* stepped: the base PMF times the fine-structure weights p_c / smooth(p_c) of the
  component PMF p_c, renormalized. The base PMF keeps the level and width, and the
  component PMF adds only the support pattern (for example 5-point steps).

The forecast is the mixture w_base * base + w_stepped * stepped. After each match the weights move by
w <- w * p(y)^eta per alliance, then fixed share w <- (1 - alpha) w + alpha / 2. At a season
start w <- (1 - lam) w + lam / 2. The weights carry across seasons.
"""

import math
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from backend.common.helpers.predictions_v2.model.rulebook import (
    component_value,
    SCORE_COMPONENTS,
    ScoreComponent,
)
from backend.common.helpers.predictions_v2.model.state import register_state
from backend.common.helpers.predictions_v2.model.types import AllianceBreakdown
from backend.common.models.keys import TeamKey, Year

MIN_READY = 60  # alliance breakdowns before the component PMF is used
N_BINS = 16  # strength-ratio bins, edges 0 .. 3.2
BIN_W = 0.2
HIST_A = 2.0  # Dirichlet pseudo count of a bin histogram toward the pooled histogram
TEAM_N0 = 4.0  # pseudo count of a team rate toward the season mean / 3
TEAM_MIN_W = 1.0 / 30.0
G_MIN_W = 1.0 / 500.0
BETAS = np.array([0.0, 0.08, 0.16, 0.25, 0.35, 0.5, 0.7])
GH_X, _GH_W = np.polynomial.hermite_e.hermegauss(7)
GH_W: np.ndarray = _GH_W / _GH_W.sum()
SMOOTH_W = 11  # odd window of the centered moving average in the stepped weights
FLOOR = 1e-6  # floor of p(y) in the mixture update


@register_state
class _Comp:
    def __init__(self, spec: ScoreComponent) -> None:
        self.name = spec.field
        self.step = int(spec.step)
        self.po_only = bool(spec.playoff_only)
        self.maxc = 8
        self.hist: np.ndarray = np.zeros((N_BINS, self.maxc + 1))
        self.g = 0.0  # season mean count per alliance
        self.gn = 0.0

    def grow(self, c: int) -> None:
        if c > self.maxc:
            new = max(c, int(self.maxc * 1.5) + 1)
            h = np.zeros((N_BINS, new + 1))
            h[:, : self.maxc + 1] = self.hist
            self.hist = h
            self.maxc = new


def _bin_pos(ratio: float) -> Tuple[int, int, float]:
    x = min(max(ratio / BIN_W - 0.5, 0.0), N_BINS - 1.0)
    i = int(math.floor(x))
    return i, min(i + 1, N_BINS - 1), x - i


@register_state
class ComponentModel:
    """Per-season component count model on the season's score components."""

    def __init__(self, specs: Sequence[ScoreComponent]) -> None:
        self.comps = [_Comp(s) for s in specs]
        self.rates: Dict[TeamKey, np.ndarray] = {}
        self.rn: Dict[TeamKey, np.ndarray] = {}
        self.n_obs = 0

    def ready(self) -> bool:
        return self.n_obs >= MIN_READY

    def _mu(self, teams: Sequence[TeamKey]) -> np.ndarray:
        g3 = np.array([c.g / 3.0 for c in self.comps])
        mu = np.zeros(len(self.comps))
        for t in teams:
            r = self.rates.get(t)
            if r is None:
                mu += g3
            else:
                n = self.rn[t]
                mu += (n * r + TEAM_N0 * g3) / (n + TEAM_N0)
        for k, c in enumerate(self.comps):
            if c.po_only:
                mu[k] = c.g
        return mu

    def _ratios(self, teams: Sequence[TeamKey]) -> np.ndarray:
        mu = self._mu(teams)
        return np.array(
            [
                mu[k] / max(c.g, 1e-6) if c.gn > 0 else 1.0
                for k, c in enumerate(self.comps)
            ]
        )

    @staticmethod
    def _comp_pmfs(c: _Comp, ratio: np.ndarray) -> np.ndarray:
        """Count PMFs of one component at an array of strength ratios."""
        x = np.clip(ratio / BIN_W - 0.5, 0.0, N_BINS - 1.0)
        i = np.floor(x).astype(int)
        j = np.minimum(i + 1, N_BINS - 1)
        f = (x - i)[..., None]
        pooled = c.hist.sum(0) + 1e-3
        pooled = pooled / pooled.sum()
        tab = c.hist + HIST_A * pooled
        tab = tab / tab.sum(1, keepdims=True)
        return np.asarray((1 - f) * tab[i] + f * tab[j])

    def forecast(
        self, teams: Sequence[TeamKey], is_po: bool, m: float, sd: float
    ) -> Optional[np.ndarray]:
        """Alliance score PMF on 0..L with mean m, or None if the mean anchor fails."""
        comps = [(k, c) for k, c in enumerate(self.comps) if is_po or not c.po_only]
        L = 1 + sum(c.maxc * c.step for _, c in comps)
        nfft = 1 << int(math.ceil(math.log2(L + 1)))
        ratios0 = self._ratios(teams)[[k for k, _ in comps]]
        load = np.exp(
            np.outer(BETAS, GH_X)
        )  # (beta, node) factor on the strength ratio
        # Component count PMFs per (beta, node). The components are independent given the
        # node, so the mean and variance of their sum are exact sums. The loading beta whose
        # mixture sd is closest to sd is chosen from these moments.
        pcs: List[np.ndarray] = []
        mom = np.zeros((len(BETAS), len(GH_X), 2))
        for idx, (_, c) in enumerate(comps):
            r = np.full(load.shape, ratios0[idx]) if c.po_only else ratios0[idx] * load
            pc = self._comp_pmfs(c, r)  # (beta, node, maxc + 1)
            pts = c.step * np.arange(pc.shape[-1], dtype=float)
            mu_c = pc @ pts
            mom[:, :, 0] += mu_c
            mom[:, :, 1] += pc @ (pts * pts) - mu_c * mu_c
            pcs.append(pc)
        m_b = mom[:, :, 0] @ GH_W
        v_b = (mom[:, :, 1] + mom[:, :, 0] ** 2) @ GH_W - m_b**2
        bi = int(np.argmin(np.abs(np.sqrt(np.maximum(v_b, 0.0)) - sd)))
        spec_prod = np.ones((len(GH_X), nfft // 2 + 1), dtype=complex)
        for idx, (_, c) in enumerate(comps):
            pc = pcs[idx][bi]  # (node, maxc + 1)
            n = min(pc.shape[1], (nfft - 1) // c.step + 1)
            grid = np.zeros((len(GH_X), nfft))
            grid[:, : n * c.step : c.step] = pc[:, :n]
            spec_prod *= np.fft.rfft(grid, axis=-1)
        pmfs = np.clip(np.fft.irfft(spec_prod, n=nfft, axis=-1)[:, : L + 1], 0.0, None)
        p = GH_W @ pmfs
        p = p / p.sum()
        sc = max(sd, 1.0)
        w, mu_t = _tilt(p, m, sc)
        if abs(mu_t - m) > 0.25 * sc:
            return None
        return w

    def update(
        self, teams: Sequence[TeamKey], is_po: bool, bd: Optional[AllianceBreakdown]
    ) -> None:
        if bd is None:
            return
        try:
            vals = [float(component_value(bd, c.name)) for c in self.comps]
        except (TypeError, ValueError):
            return
        mu = self._mu(teams)
        ratios = self._ratios(teams)
        for k, c in enumerate(self.comps):
            if c.po_only and not is_po:
                continue
            v = vals[k]
            if not math.isfinite(v) or v < 0 or v % c.step:
                continue
            cnt = int(v // c.step)
            c.grow(cnt)
            i, j, f = _bin_pos(ratios[k])
            c.hist[i, cnt] += 1 - f
            c.hist[j, cnt] += f
            c.gn += 1
            c.g += max(1.0 / c.gn, G_MIN_W) * (cnt - c.g)
            if not c.po_only:
                e = cnt - mu[k]
                for t in teams:
                    if t not in self.rates:
                        self.rates[t] = np.array([cc.g / 3.0 for cc in self.comps])
                        self.rn[t] = np.zeros(len(self.comps))
                    self.rn[t][k] += 1
                    self.rates[t][k] += (
                        max(1.0 / (self.rn[t][k] + TEAM_N0), TEAM_MIN_W)
                        * e
                        / len(teams)
                    )
        self.n_obs += 1


def _smooth(p: np.ndarray) -> np.ndarray:
    """Centered moving average with an odd window (an even window shifts the mean)."""
    return np.convolve(p, np.ones(SMOOTH_W) / SMOOTH_W, mode="same")


def _tilt(
    p: np.ndarray, m: float, sc: float, tol: float = 1e-3
) -> Tuple[np.ndarray, float]:
    """Exponential tilt p(y) exp(theta y / sc) with mean m (bisection on theta in [-6, 6]).

    The tilt keeps the support, so it moves the mean without moving mass off the score
    steps. Returns (PMF, its mean).
    """
    ks = np.arange(len(p), dtype=float)
    logp = np.log(np.maximum(p, 1e-300))

    def tilt(th: float) -> Tuple[np.ndarray, float]:
        lw = logp + th * ks / sc
        w = np.exp(lw - lw.max())
        w = w / w.sum()
        return w, float(w @ ks)

    lo, hi = -6.0, 6.0
    w, mu_t = tilt(0.0)
    if abs(mu_t - m) > tol:
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            w, mu_t = tilt(mid)
            if mu_t < m:
                lo = mid
            else:
                hi = mid
            if abs(mu_t - m) < tol:
                break
    return w, mu_t


def _pad(a: np.ndarray, n: int, value: float = 0.0) -> np.ndarray:
    return np.pad(a, (0, n - len(a)), constant_values=value)


@register_state
class ScoreStructure:
    """The causal {base, stepped} mixture over the season's component model."""

    def __init__(self, eta: float, alpha: float, lam: float) -> None:
        self.eta = float(eta)
        self.alpha = float(alpha)
        self.lam = float(lam)
        self.w: np.ndarray = np.array([0.5, 0.5])  # weights of (base, stepped)
        self.cm: Optional[ComponentModel] = None

    def start_season(self, season: Year) -> None:
        self.w = (1.0 - self.lam) * self.w + self.lam / 2.0
        specs = SCORE_COMPONENTS.get(season)
        self.cm = ComponentModel(specs) if specs else None

    def arms(
        self,
        pe: np.ndarray,
        teams: Sequence[TeamKey],
        is_po: bool,
        m: float,
        sd: float,
    ) -> Optional[np.ndarray]:
        """The stepped PMF for one alliance, or None before the component model is ready."""
        if self.cm is None or not self.cm.ready():
            return None
        pa = self.cm.forecast(teams, is_po, m, sd)
        if pa is None:
            return None
        sp = _smooth(pa)
        # FFT round-off leaves noise below ~1e-12 in pa. Use weight 1 there.
        ws = np.where(sp > 1e-10, pa / np.maximum(sp, 1e-300), 1.0)
        n = max(len(pe), len(ws))
        pb = _pad(pe, n) * _pad(ws, n, 1.0)
        return pb / pb.sum()

    def mix(self, pe: np.ndarray, pb: Optional[np.ndarray]) -> np.ndarray:
        """Mixture of the arms, tilted to the mean of the base PMF."""
        if pb is None:
            return pe
        n = max(len(pe), len(pb))
        pm = self.w[0] * _pad(pe, n) + self.w[1] * _pad(pb, n)
        ks = np.arange(len(pe), dtype=float)
        m = float(pe @ ks)
        sc = max(math.sqrt(max(float(pe @ (ks * ks)) - m * m, 0.0)), 1.0)
        return _tilt(pm, m, sc, tol=1e-6)[0]

    def learn(
        self, rows: Sequence[Tuple[np.ndarray, Optional[np.ndarray], int]]
    ) -> None:
        """Move the weights with the pre-match (base, stepped) PMFs of each alliance."""
        for pe, pb, y in rows:
            if pb is None:
                continue  # both arms equal the base PMF: the weights do not move
            lp = np.array(
                [
                    math.log(max(float(p[y]) if 0 <= y < len(p) else 0.0, FLOOR))
                    for p in (pe, pb)
                ]
            )
            lw = np.log(np.maximum(self.w, 1e-300)) + self.eta * lp
            w = np.exp(lw - lw.max())
            self.w = w / w.sum()
        self.w = (1.0 - self.alpha) * self.w + self.alpha / 2.0

    def observe(
        self, teams: Sequence[TeamKey], is_po: bool, bd: Optional[AllianceBreakdown]
    ) -> None:
        """Feed one alliance result to the component model."""
        if self.cm is not None:
            self.cm.update(teams, is_po, bd)
