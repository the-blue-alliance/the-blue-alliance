"""Rules-free score structure for the hkf score PMF (experiments E2c and E2-sel).

No game rules, field names or hand-written specs are used. The inputs are the past alliance
``score_breakdown`` dicts of the season and the alliance totals.

Discovery (``Discoverer``), run on the breakdowns seen so far in the season:

1. Candidate fields: numeric (int or float, not bool), non-negative on every row, not always
   0, and not equal to the total on >= 99% of rows (that is a total field).
2. Field set: binary x_k with sum_k x_k * f_k(row) = total(row) + slack(row). A MILP maximizes
   the number of selected fields minus a large penalty on slack. Sub-total fields lose to their
   parts, because the parts give more selected fields.
3. Accept the set only if it reproduces the total exactly on >= ACCEPT of the rows.
4. Step per field: the gcd of the values that occur at least twice.
5. Playoff-only: a field that is 0 on every qualification row but non-zero in a playoff row.

Discovery runs every REDISCOVER new breakdowns until a set is accepted, then every RECHECK.
When the accepted set changes, the component model is rebuilt from this season's stored
results (past matches only).

Component model (``ComponentModel``): per component, a count histogram per bin of the team
strength ratio (team component rates over the season mean). A shared latent alliance factor
(Gauss-Hermite nodes, loading beta chosen so that the PMF sd matches the base sd) couples the
components. The alliance PMF is the FFT convolution of the component PMFs, tilted so that its
mean equals the base mean.

Score PMF arms (``ScoreStructure``):

* ``e3``: the base PMF (no structure).
* ``e2cb``: the base PMF times the fine-structure weights p_c / smooth(p_c) of the component
  PMF p_c, renormalized. The base PMF keeps the level and width, and the component PMF adds
  only the support pattern (for example 5-point steps).

The forecast is the mixture w_e3 * e3 + w_e2cb * e2cb. After each match the weights move by
w <- w * p(y)^eta per alliance, then fixed share w <- (1 - alpha) w + alpha / 2. At a season
start w <- (1 - lam) w + lam / 2. The weights carry across seasons.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

# ---- Discovery
ACCEPT = 0.99  # fraction of rows that the field set must reproduce exactly
MIN_ROWS = 24  # alliance breakdowns before the first discovery
MAX_ROWS = 300  # most recent rows used in the MILP
REDISCOVER = 12  # new breakdowns between discoveries before a set is accepted
RECHECK = 200  # new breakdowns between discoveries after a set is accepted
MILP_TIME = 20.0  # seconds

# ---- Component model
MIN_READY = 60  # alliance breakdowns before the component PMF is used
N_BINS = 16  # strength-ratio bins, edges 0 .. 3.2
BIN_W = 0.2
HIST_A = 2.0  # Dirichlet pseudo count of a bin histogram toward the pooled histogram
TEAM_N0 = 4.0  # pseudo count of a team rate toward the season mean / 3
TEAM_MIN_W = 1.0 / 30.0
G_MIN_W = 1.0 / 500.0
BETAS = np.array([0.0, 0.08, 0.16, 0.25, 0.35, 0.5, 0.7])
GH_X, GH_W = np.polynomial.hermite_e.hermegauss(7)
GH_W = GH_W / GH_W.sum()
SMOOTH_W = 11  # odd window of the centered moving average in the e2cb weights
FLOOR = 1e-6  # floor of p(y) in the mixture update

Row = Tuple[Dict[str, float], float, bool]


def numeric_fields(bd: dict) -> Dict[str, float]:
    """Top-level numeric fields of a breakdown dict (bools and non-finite values excluded)."""
    out = {}
    for k, v in bd.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        if isinstance(v, float) and not math.isfinite(v):
            continue
        out[k] = float(v)
    return out


def step_of(v: np.ndarray) -> int:
    """gcd of the positive values that occur at least twice (all positive values if none)."""
    vals, cnt = np.unique(np.round(v).astype(int), return_counts=True)
    rep = [int(x) for x, c in zip(vals, cnt) if c >= 2 and x > 0]
    if not rep:
        rep = [int(x) for x in vals if x > 0]
    if not rep:
        return 1
    return max(1, int(np.gcd.reduce(rep)))


def discover(rows: Sequence[Row]) -> Optional[List[dict]]:
    """Component specs from (numeric fields, total, is_playoff) rows, or None."""
    if len(rows) < MIN_ROWS:
        return None
    rows = list(rows)[-MAX_ROWS:]
    keys = sorted(set().union(*[set(r[0]) for r in rows]))
    if not keys:
        return None
    F = np.array([[r[0].get(k, np.nan) for k in keys] for r in rows], float)
    y = np.array([r[1] for r in rows], float)
    ok = (
        np.all(np.isfinite(F), axis=0) & np.all(F >= 0, axis=0) & np.any(F != 0, axis=0)
    )
    ok &= ~(np.mean(np.isclose(F, y[:, None]), axis=0) >= 0.99)
    idx = np.where(ok)[0]
    if len(idx) == 0:
        return None
    A = F[:, idx]
    n, K = A.shape
    # Variables: x (K binary), s+ (n), s- (n). A x - s+ + s- = y.
    big = 1000.0
    c = np.concatenate([-np.ones(K), big * np.ones(2 * n)])
    cons = LinearConstraint(np.hstack([A, -np.eye(n), np.eye(n)]), y, y)
    integrality = np.concatenate([np.ones(K), np.zeros(2 * n)])
    bounds = Bounds(
        np.zeros(K + 2 * n), np.concatenate([np.ones(K), np.full(2 * n, np.inf)])
    )
    res = milp(
        c,
        constraints=[cons],
        integrality=integrality,
        bounds=bounds,
        options={"time_limit": MILP_TIME},
    )
    if res.x is None:
        return None
    sel = idx[np.round(res.x[:K]) > 0.5]
    if len(sel) == 0:
        return None
    if np.mean(np.isclose(F[:, sel].sum(1), y)) < ACCEPT:
        return None
    po = np.array([r[2] for r in rows])
    specs = []
    for j in sel:
        v = F[:, j]
        po_only = bool(
            (~po).any() and po.any() and np.all(v[~po] == 0) and np.any(v[po] != 0)
        )
        specs.append({"name": keys[j], "step": step_of(v), "playoff_only": po_only})
    return specs


class Discoverer:
    """Online discovery state for one season."""

    def __init__(self) -> None:
        self.rows: List[Row] = []
        # Every alliance result of the season: (teams, is_playoff, breakdown, total).
        self.hist: List[Tuple[Tuple[str, ...], bool, Optional[dict], float]] = []
        self.specs: Optional[List[dict]] = None
        self.since = 0
        self.wait = (
            REDISCOVER  # breakdowns until the next search while no set is accepted
        )
        self.changes = 0

    def observe(
        self, teams: Sequence[str], is_po: bool, bd: Optional[dict], y: float
    ) -> bool:
        """Store one alliance result. Return True when the accepted field set changed."""
        self.hist.append((tuple(teams), is_po, bd, float(y)))
        if isinstance(bd, dict):
            self.rows.append((numeric_fields(bd), float(y), is_po))
            self.since += 1
        if self.since < (RECHECK if self.specs is not None else self.wait):
            return False
        self.since = 0
        new = discover(self.rows)
        if new is None:
            if self.specs is None and len(self.rows) >= MIN_ROWS:
                # No field set fits (for example a game whose total is not a sum of fields):
                # search less often, so a season without a set costs O(log n) searches.
                self.wait = min(2 * self.wait, RECHECK)
            return False
        sig = [(s["name"], s["step"], s["playoff_only"]) for s in new]
        if sig == [
            (s["name"], s["step"], s["playoff_only"]) for s in (self.specs or [])
        ]:
            return False
        self.specs = new
        self.changes += 1
        return True


class _Comp:
    def __init__(self, spec: dict) -> None:
        self.name = spec["name"]
        self.step = int(spec["step"])
        self.po_only = bool(spec["playoff_only"])
        self.maxc = 8
        self.hist = np.zeros((N_BINS, self.maxc + 1))
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


class ComponentModel:
    """Per-season component count model on a discovered field set."""

    def __init__(self, specs: List[dict]) -> None:
        self.comps = [_Comp(s) for s in specs]
        self.rates: Dict[str, np.ndarray] = {}
        self.rn: Dict[str, np.ndarray] = {}
        self.n_obs = 0

    def ready(self) -> bool:
        return self.n_obs >= MIN_READY

    def _mu(self, teams: Sequence[str]) -> np.ndarray:
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

    def _ratios(self, teams: Sequence[str]) -> np.ndarray:
        mu = self._mu(teams)
        return np.array(
            [
                mu[k] / max(c.g, 1e-6) if c.gn > 0 else 1.0
                for k, c in enumerate(self.comps)
            ]
        )

    @staticmethod
    def _comp_pmfs(c: _Comp, ratio: np.ndarray) -> np.ndarray:
        """Count PMFs of one component at an array of strength ratios (interpolated between bins)."""
        x = np.clip(ratio / BIN_W - 0.5, 0.0, N_BINS - 1.0)
        i = np.floor(x).astype(int)
        j = np.minimum(i + 1, N_BINS - 1)
        f = (x - i)[..., None]
        pooled = c.hist.sum(0) + 1e-3
        pooled = pooled / pooled.sum()
        tab = c.hist + HIST_A * pooled
        tab = tab / tab.sum(1, keepdims=True)
        return (1 - f) * tab[i] + f * tab[j]

    def forecast(
        self, teams: Sequence[str], is_po: bool, m: float, sd: float
    ) -> Optional[np.ndarray]:
        """Alliance score PMF on 0..L with mean m, or None if the mean anchor fails. Read-only."""
        comps = [(k, c) for k, c in enumerate(self.comps) if is_po or not c.po_only]
        L = 1 + sum(c.maxc * c.step for _, c in comps)
        nfft = 1 << int(math.ceil(math.log2(L + 1)))
        ratios0 = self._ratios(teams)[[k for k, _ in comps]]
        load = np.exp(
            np.outer(BETAS, GH_X)
        )  # (beta, node) factor on the strength ratio
        # Component count PMFs per (beta, node). The components are independent given the node,
        # so the mean and variance of their sum are exact sums. The loading beta whose mixture sd
        # is closest to sd is chosen from these moments. Only that beta needs the FFT.
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

    def update(self, teams: Sequence[str], is_po: bool, bd: Optional[dict]) -> None:
        if not isinstance(bd, dict):
            return
        try:
            vals = [float(bd[c.name]) for c in self.comps]
        except (KeyError, TypeError, ValueError):
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

    The tilt keeps the support, so it moves the mean without moving mass off the score steps.
    The tilted mean increases with theta, so bisection converges. Returns (PMF, its mean).
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


class ScoreStructure:
    """E2c discovery plus the causal {e3, e2cb} mixture. One instance per model."""

    def __init__(self, eta: float, alpha: float, lam: float) -> None:
        self.eta, self.alpha, self.lam = float(eta), float(alpha), float(lam)
        self.w = np.array([0.5, 0.5])  # weights of (e3, e2cb)
        self.disc = Discoverer()
        self.cm: Optional[ComponentModel] = None

    def start_season(self) -> None:
        self.w = (1.0 - self.lam) * self.w + self.lam / 2.0
        self.disc = Discoverer()
        self.cm = None

    def arms(
        self, pe: np.ndarray, teams: Sequence[str], is_po: bool, m: float, sd: float
    ) -> Optional[np.ndarray]:
        """The e2cb PMF for one alliance, or None before the component model is ready."""
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
        """Mixture of the arms, tilted to the mean of the base PMF.

        The e2cb weights p_c / smooth(p_c) can move the mean by a fraction of a point. The tilt
        keeps the point forecast (the PMF mean) at the base mean and keeps the support pattern.
        """
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
        """Move the weights with the pre-match (e3, e2cb) PMFs of each alliance of one match."""
        for pe, pb, y in rows:
            if pb is None:
                continue  # both arms equal e3: the weights do not move
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
        self, teams: Sequence[str], is_po: bool, bd: Optional[dict], y: float
    ) -> None:
        """Feed one alliance result to discovery and the component model."""
        if self.disc.observe(teams, is_po, bd, y):
            self.cm = ComponentModel(self.disc.specs or [])
            for (
                t_,
                po_,
                bd_,
                _,
            ) in self.disc.hist:  # rebuild from this season's past results
                self.cm.update(t_, po_, bd_)
        elif self.cm is not None:
            self.cm.update(teams, is_po, bd)
