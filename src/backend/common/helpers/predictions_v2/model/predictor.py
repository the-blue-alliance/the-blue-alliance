"""HKF: a hierarchical Kalman filter FRC match predictor.

Each team has a two-dimensional latent strength per season, in units of the season's
alliance-score standard deviation (sigma):

* ``s``: contribution to the shared alliance score (game pieces, bonuses).
* ``u``: points the rulebook attributes to this robot alone (auto mobility, endgame climb or
  park). The TBA breakdown records these per driver station.

Observations per alliance: the shared score (total minus robot points minus foul points
received) and one robot-points value per station. Foul points depend on the opponent, so
they enter the forecast as a season mean and a noise term only.

Within an event, the filter keeps a full covariance over all teams at that event. Between
events and seasons, only each team's marginal state is kept.

Win probability:

1. The filter gives a margin mean ``d`` and variance ``v``.
2. An empirical, symmetric CDF of standardized margin residuals maps ``d/sqrt(v)`` to a
   probability. The CDF is learned online (normal prior, pooled past seasons, current
   season).
3. An online Bayesian logistic regression (the stacker) combines that logit with a slow
   win-outcome rating and antisymmetric red - blue features, among them a cross-event
   rating from per-event conjugate-gradient solves (PCG). The weights drift.

Scores: a PMF on the integers >= 0, ``mean + sd * T`` with a learned residual shape ``T``
(Gaussian mixtures per score-level bucket), mixed with the rulebook score-component
structure. The mean is the filter forecast plus an event-progress offset, online
recalibrations and a foul-transfer term.

Ranking points (qualification matches): win and tie RP values times their probabilities
plus bonus RP probabilities from the rulebook model (``bonus.py``), with an online logistic
model (``rp.py``) as the fallback. ``median_rp`` is the median of a joint RP PMF.

Every online learner uses only matches that were played before the forecast, and
``predict_match`` never changes state.
"""

import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from backend.common.consts.event_type import EventType
from backend.common.helpers.predictions_v2.model import state
from backend.common.helpers.predictions_v2.model.bonus import (
    RuleBonusModel,
    tier_of,
    TIER_THRESHOLDS,
)
from backend.common.helpers.predictions_v2.model.config import (
    DEFAULT_CONFIG,
    HKFConfig,
)
from backend.common.helpers.predictions_v2.model.gmm_shape import (
    BucketGmmShape,
    GmmShape,
)
from backend.common.helpers.predictions_v2.model.rp import BonusModel, OnlineLogit
from backend.common.helpers.predictions_v2.model.rp_pmf import rp_values, RPJoint
from backend.common.helpers.predictions_v2.model.rulebook import (
    foul_points,
    playoff_bonus_points,
    ROBOT_POINT_SEASONS,
    robot_points,
    SCORE_COMPONENTS,
)
from backend.common.helpers.predictions_v2.model.structure import ScoreStructure
from backend.common.helpers.predictions_v2.model.types import (
    MatchContext,
    MatchOutcome,
    MatchPrediction,
    RankingPointsPrediction,
    ScoreDistribution,
)
from backend.common.models.keys import EventKey, TeamKey, Year

# Bump when a code change alters predictions. A stored state of another version is not
# loaded: the season is replayed from the match log instead.
MODEL_VERSION = "hkf-1"

Hyper = Dict[str, float]
# Shape bucket: (score-level bin, is qualification).
ShapeKey = Tuple[int, bool]
# (s, u) mean, 2x2 covariance, season and event of a team's latest state.
TeamState = Tuple[np.ndarray, np.ndarray, Year, EventKey]
# Per-event PCG normal equations: rows of A^T A, A^T b and the solved ratings.
EventPCG = Tuple[
    Dict[TeamKey, Dict[TeamKey, float]], Dict[TeamKey, float], Dict[TeamKey, float]
]

# Numerical settings.
SHAPE_SUPPORT = (
    8.0  # half-width (sd units) of the margin CDF and of the residual shapes
)
MARGIN_BIN_W = 0.05  # bin width (sd units) of the empirical margin CDF
PROG_BINS = 12  # event-progress offset bins (matches already played at the event)
LEVEL_EDGES = (0.0, 0.75)  # forecast-level edges of the residual shape buckets

SAT_DIM = 6
STACK_DIM = 12


def model_fingerprint(cfg: HKFConfig) -> str:
    return state.fingerprint(
        cfg,
        MODEL_VERSION,
        SCORE_COMPONENTS,
        sorted(ROBOT_POINT_SEASONS),
        TIER_THRESHOLDS,
    )


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _solve_pcg_dict(
    ata: Dict[TeamKey, Dict[TeamKey, float]],
    atb: Dict[TeamKey, float],
    reg: float,
    x0: Dict[TeamKey, float],
    iters: int,
) -> Dict[TeamKey, float]:
    """Warm-started conjugate gradient solver for (A^T A + reg * I) x = A^T b."""
    teams = list(atb.keys())
    if not teams:
        return {}
    x = {t: x0.get(t, 0.0) for t in teams}
    r: Dict[TeamKey, float] = {}
    for t in teams:
        ax = reg * x[t] + sum(w * x[u] for u, w in ata.get(t, {}).items())
        r[t] = atb[t] - ax
    d = dict(r)
    rs_old = sum(v * v for v in r.values())
    if rs_old < 1e-12:
        return x
    for _ in range(iters):
        ad: Dict[TeamKey, float] = {}
        dad = 0.0
        for t in teams:
            v = reg * d[t] + sum(w * d[u] for u, w in ata.get(t, {}).items())
            ad[t] = v
            dad += d[t] * v
        if dad <= 1e-12:
            break
        alpha = rs_old / dad
        rs_new = 0.0
        for t in teams:
            x[t] += alpha * d[t]
            r[t] -= alpha * ad[t]
            rs_new += r[t] * r[t]
        if rs_new < 1e-10:
            break
        beta = rs_new / rs_old
        for t in teams:
            d[t] = r[t] + beta * d[t]
        rs_old = rs_new
    return x


@state.register_state
class _Run:
    """Running mean and variance with a pseudo-count prior and an optional floor weight
    on the mean.

    It also keeps the centered (Welford) moments of the data alone, with no prior.
    """

    __slots__ = ("mean", "n", "var", "wm", "wm2")

    def __init__(self) -> None:
        self.n = 0
        self.mean = 0.0
        self.var = 1.0
        self.wm = 0.0
        self.wm2 = 0.0

    def add(self, x: float, prior_n: float, min_w: float, prior_nv: float) -> None:
        self.n += 1
        w = max(1.0 / (self.n + prior_n), min_w)
        d = x - self.mean
        self.mean += w * d
        wv = 1.0 / (self.n + prior_nv)
        self.var += wv * (d * d - self.var)
        wc = 1.0 / self.n
        dw = x - self.wm
        self.wm += wc * dw
        self.wm2 = (1.0 - wc) * (self.wm2 + wc * dw * dw)

    @property
    def data_var(self) -> float:
        """Centered variance of the observed data (0 before 2 points)."""
        return self.wm2 if self.n > 1 else 0.0


@state.register_state
class _EventState:
    """Joint Gaussian state of every team at one event: mean and covariance over [s, u]."""

    __slots__ = ("cov", "idx", "mu", "n")

    def __init__(self, cap: int = 128) -> None:
        self.idx: Dict[TeamKey, int] = {}  # team -> base index (s at i, u at i + 1)
        self.mu: np.ndarray = np.zeros(cap)
        self.cov: np.ndarray = np.zeros((cap, cap))
        self.n = 0

    def add(self, team: TeamKey, m: np.ndarray, P: np.ndarray) -> int:
        """Append a team with marginal mean m and covariance P, uncorrelated with the others."""
        if self.n + 2 > len(self.mu):
            cap = 2 * len(self.mu)
            mu = np.zeros(cap)
            mu[: self.n] = self.mu[: self.n]
            cov = np.zeros((cap, cap))
            cov[: self.n, : self.n] = self.cov[: self.n, : self.n]
            self.mu, self.cov = mu, cov
        i = self.n
        self.idx[team] = i
        self.mu[i : i + 2] = m
        self.cov[i : i + 2, :] = 0.0
        self.cov[:, i : i + 2] = 0.0
        self.cov[i : i + 2, i : i + 2] = P
        self.n += 2
        return i


@state.register_state
class HKFPredictor:
    """The HKF match predictor (see the module docstring and
    docs/Developing/Predictions-v2-Model.md).

    Lifecycle: ``start_season`` at each season change (it rolls the finished season into
    the cross-season priors), then for every match in stream order ``predict_match`` before
    ``update`` with its result.
    """

    def __init__(self, cfg: HKFConfig = DEFAULT_CONFIG) -> None:
        self.cfg = cfg
        c = cfg
        self.teams: Dict[TeamKey, TeamState] = {}
        self.events: Dict[EventKey, _EventState] = {}
        self.season: Optional[Year] = None
        self.prev_mean: Optional[float] = None
        self.prev_cv = 0.5
        self.hist: Dict[TeamKey, List[Tuple[Year, float]]] = {}
        self._shape_init()
        self.wr: Dict[TeamKey, float] = {}  # win rating (no decay across seasons)
        pvs = [c.stack_pv] * STACK_DIM
        pvs[-3:] = [c.stack_po_pv] * 3
        self.stacker = OnlineLogit(
            STACK_DIM,
            pvs,
            c.stack_q,
            prior_mean=[1.0] + [0.0] * (STACK_DIM - 1),
            q_all=True,
        )
        self.ag_hist: List[np.ndarray] = []  # final rank weights of past seasons
        self.ag_prior: np.ndarray = np.zeros(4)
        self.sat_xx_pool: np.ndarray = np.zeros((SAT_DIM, SAT_DIM))
        self.sat_xe_pool: np.ndarray = np.zeros(SAT_DIM)
        self.sat_w: np.ndarray = np.zeros(SAT_DIM)
        self.qm_s_mean: np.ndarray = np.array([0.55, -0.03, -0.58, 0.09])
        self.qm_s_n = 100.0
        self.scount: Dict[TeamKey, int] = {}  # matches played this season, per team
        # team -> (earlier events this season, current event)
        self.nevc: Dict[TeamKey, Tuple[int, EventKey]] = {}
        self.bonus = BonusModel([c.rp_prior_var] * 4, c.rp_q)
        self.rbonus = RuleBonusModel(c)
        self.rpj = RPJoint(rho_prior=c.rp_rho_prior, rho_prior_sd=c.rp_rho_sd)
        self.gmm = GmmShape(SHAPE_SUPPORT, c.gmm_k, c.gmm_kn, c.gmm_kp, c.gmm_sdscale)
        # Shape buckets, all created here so that predict_match never changes state.
        self.gmm_b: Dict[ShapeKey, BucketGmmShape] = {}
        for xk in (0, 1, 2):
            for lk in (True, False):
                self.gmm_b[(xk, lk)] = BucketGmmShape(
                    self.gmm,
                    c.gmm_cond_kg,
                    SHAPE_SUPPORT,
                    c.gmm_k,
                    c.gmm_kp,
                    c.gmm_sdscale,
                )
        # Past seasons' centered progress offsets: sum r/sig, n.
        self.pg_pool: np.ndarray = np.zeros((2, PROG_BINS))
        self.struct = ScoreStructure(c.struct_eta, c.struct_alpha, c.struct_lam)
        self._new_season_stats()

    # ------------------------------------------------------------------ state
    def encode_state(self) -> bytes:
        return state.encode(self, model_fingerprint(self.cfg))

    @classmethod
    def decode_state(
        cls, blob: bytes, cfg: HKFConfig = DEFAULT_CONFIG
    ) -> "HKFPredictor":
        """Raises ``state.StateVersionError`` for a state of another model version."""
        obj = state.decode(blob, model_fingerprint(cfg), cfg)
        if not isinstance(obj, cls):
            raise state.StateVersionError(f"not a {cls.__name__} state")
        return obj

    def drop_events(self, event_keys: Iterable[EventKey]) -> None:
        """Forget the within-event state of finished events.

        Only a match of that event reads the state, so outputs do not change while no
        further match of the event arrives.
        """
        gone = set(event_keys)
        if not gone:
            return
        for ek in gone:
            self.events.pop(ek, None)
        self.ecount = {k: v for k, v in self.ecount.items() if k[0] not in gone}
        self.po_res = {k: v for k, v in self.po_res.items() if k[0] not in gone}

    def _new_season_stats(self) -> None:
        self.n = 0
        self.tot = _Run()  # raw alliance totals
        self.Ls = 0.0  # shared level (points per alliance), residual driven
        self.Lu = 0.0  # robot level (points per robot), residual driven
        self.nu = 0
        self.foul = _Run()  # foul points received per alliance
        self.sh = _Run()  # raw shared points per alliance (spread)
        self.rob = _Run()  # raw robot points (spread)
        self.rs_sum = 0.0  # sum of (e_s^2 - model var), points^2
        self.rs_n = 0
        self.ru_sum = 0.0
        self.ru_n = 0
        self.g_xy = 0.0
        self.g_xx = 0.0
        # Score calibration sums: n, sum x, sum x^2, sum e, sum x e.
        self.sc: np.ndarray = np.zeros(5)
        # Variance calibration sums: n, sum x, sum x^2, sum z^2, sum x z^2.
        self.vc: np.ndarray = np.zeros(5)
        # team -> (sum of foul deviations given, n)
        self.fteam: Dict[TeamKey, Tuple[float, float]] = {}
        self.pg_cur: np.ndarray = np.zeros((2, PROG_BINS))  # this season: sum r/sig, n
        self.ecount: Dict[Tuple[EventKey, TeamKey], int] = {}  # matches played
        self.comp = self.season in ROBOT_POINT_SEASONS
        self.ag_xx: np.ndarray = np.zeros((4, 4))  # rank-weight regression sums
        self.ag_xe: np.ndarray = np.zeros(4)
        self.sat_xx_cur: np.ndarray = np.zeros((SAT_DIM, SAT_DIM))
        self.sat_xe_cur: np.ndarray = np.zeros(SAT_DIM)
        self._refresh_sat_w()
        # Cross-event PCG normal equations (season-wide and per event).
        self.s_ata: Dict[TeamKey, Dict[TeamKey, float]] = {}
        self.s_atb: Dict[TeamKey, float] = {}
        self.pcg_z: Dict[TeamKey, float] = {}
        self.team_events: Dict[TeamKey, List[EventKey]] = {}
        self.team_z0: Dict[TeamKey, float] = {}
        self.ev_pcg: Dict[EventKey, EventPCG] = {}
        # Playoff alliance residuals: (event, sorted teams) -> residuals.
        self.po_res: Dict[Tuple[EventKey, Tuple[TeamKey, ...]], List[float]] = {}
        self.dq_t: Dict[TeamKey, Tuple[float, float]] = {}  # team -> (DQs, matches)

    def start_season(self, season: Year) -> None:
        """Pool the finished season into the cross-season priors and reset the season state."""
        c = self.cfg
        if self.n > 0:
            self.prev_mean = self.tot.mean
            v_end = self.tot.var
            self.prev_cv = math.sqrt(max(v_end, 1e-9)) / max(self.tot.mean, 1e-6)
            # Pooled prior of the rank weights: the mean of the past seasons' final values.
            self.ag_hist.append(self._agg_coef())
            self.ag_prior = np.mean(self.ag_hist, axis=0)
            if self.comp:
                cnt = self.pg_cur[1]
                tot_n = float(cnt.sum())
                if tot_n > 0.0:
                    mean_g = float(self.pg_cur[0].sum()) / tot_n
                    self.pg_pool[0] += self.pg_cur[0] - cnt * mean_g
                    self.pg_pool[1] += cnt
            decay_pool = c.sat_pool_decay
            self.sat_xx_pool = decay_pool * self.sat_xx_pool + self.sat_xx_cur
            self.sat_xe_pool = decay_pool * self.sat_xe_pool + self.sat_xe_cur
        ended = self.season
        if ended is not None:
            if self.s_atb:
                self.pcg_z = _solve_pcg_dict(
                    self.s_ata, self.s_atb, c.pcg_reg, self.pcg_z, iters=10
                )
                w_c = c.pcg_carry
                for t, st in list(self.teams.items()):
                    if st[2] == ended and t in self.pcg_z:
                        m, P, s, ev = st
                        cur_t = float(m.sum())
                        new_t = (1.0 - w_c) * cur_t + w_c * self.pcg_z[t]
                        self.teams[t] = (m + 0.5 * (new_t - cur_t), P, s, ev)
            # Subtract the season-end mean team drift before the carryover.
            vals = [float(st[0].sum()) for st in self.teams.values() if st[2] == ended]
            mean_t = float(np.mean(vals)) if vals else 0.0
            for t, st in list(self.teams.items()):
                if st[2] == ended:
                    m, P, s, ev = st
                    self.teams[t] = (m - 0.5 * mean_t, P, s, ev)
            for t, st in self.teams.items():
                if st[2] == ended:
                    self.hist.setdefault(t, []).append((ended, float(st[0].sum())))
            # Shrink the collinear rank weights of the stacker toward 0.
            self.stacker.w[2:4] *= 1.0 - c.stack_agg_shrink
            for j in (2, 3):
                self.stacker.S[j, j] = min(self.stacker.S[j, j], c.stack_pv)
        self.season = season
        self.bonus.reset()
        self.rbonus.reset_season(season)
        self.rpj.start_season()
        self.struct.start_season(season)
        self.gmm.roll()
        for b in self.gmm_b.values():
            b.roll()
        self._shape_roll()
        self._new_season_stats()
        self.events = {}
        self.scount = {}
        self.nevc = {}

    # ------------------------------------------------------- hyperparameters
    def _prog_bin(self, event_key: EventKey, teams: Sequence[TeamKey]) -> int:
        n = sum(self.ecount.get((event_key, t), 0) for t in teams) / max(len(teams), 1)
        return min(int(n), PROG_BINS - 1)

    def _prog_off(self, event_key: EventKey, teams: Sequence[TeamKey]) -> float:
        """Expected score residual (points) at this stage of the event."""
        b = self._prog_bin(event_key, teams)
        k = self.cfg.prog_k
        g0 = 0.0
        if self.pg_pool[1, b] > 0.0:
            g0 = float(self.pg_pool[0, b]) / (float(self.pg_pool[1, b]) + k)
        g = (float(self.pg_cur[0, b]) + k * g0) / (float(self.pg_cur[1, b]) + k)
        return self._sigma() * g

    def _gamma(self) -> float:
        return self.g_xy / (self.g_xx + self.cfg.gamma_k0)

    def _sigma(self) -> float:
        if self.n == 0:
            m = self.prev_mean if self.prev_mean is not None else 20.0
            return max(1e-6, self.prev_cv * m)
        return math.sqrt(max(self.tot.var, 1e-9))

    def _pmf_scale(self) -> float:
        """Score PMF sd factor: the centered-variance sigma over the filter sigma."""
        if self.n == 0:
            return 1.0
        k = self.cfg.var_prior_n
        nd = float(self.tot.n)
        prior_var = (self.prev_cv * max(self.tot.mean, 1e-6)) ** 2
        fix = math.sqrt(max((k * prior_var + nd * self.tot.data_var) / (k + nd), 1e-9))
        return fix / max(self._sigma(), 1e-9)

    def _mean_total(self) -> float:
        if self.n == 0:
            return self.prev_mean if self.prev_mean is not None else 20.0
        return self.tot.mean

    def _hyper(self) -> Hyper:
        """Season hyperparameters in sigma units: team spreads and noise variances."""
        c = self.cfg
        f = c.team_share
        if not self.comp:
            return {
                "ts2": f / 3.0,
                "tu2": 0.0,
                "rs": 1.0 - f,
                "ru": 0.0,
                "rf": 0.0,
                "kap": 0.0,
            }
        sig2 = self._sigma() ** 2
        k = c.hyper_n
        # Prior split before data: robot points ~ 20% of alliance variance.
        prior_rob_var = 0.2 / 3.0  # per robot, sigma units
        prior_sh_var = 0.7
        prior_foul_var = 0.1
        g = c.robot_team_share
        if self.n > 0:
            nr = self.rob.n
            vu = (k * prior_rob_var + nr * self.rob.var / sig2) / (k + nr)
            ns = self.sh.n
            vs = (k * prior_sh_var + ns * self.sh.var / sig2) / (k + ns)
            nf = self.foul.n
            vf = (k * prior_foul_var + nf * self.foul.var / sig2) / (k + nf)
            ru = (k * (1 - g) * prior_rob_var + self.ru_sum / sig2) / (k + self.ru_n)
            rs = (k * (1 - f) * prior_sh_var + self.rs_sum / sig2) / (k + self.rs_n)
        else:
            vu, vs, vf = prior_rob_var, prior_sh_var, prior_foul_var
            ru, rs = (1 - g) * prior_rob_var, (1 - f) * prior_sh_var
        ru = min(max(ru, 0.1 * vu), 0.95 * vu)
        rs = min(max(rs, 0.1 * vs), 0.95 * vs)
        tu2 = max(vu - ru, 1e-4)
        ts2 = max((vs - rs) / 3.0, 1e-4)
        return {"ts2": ts2, "tu2": tu2, "rs": rs, "ru": ru, "rf": vf, "kap": c.kappa}

    @staticmethod
    def _prior_cov(h: Hyper) -> np.ndarray:
        ts, tu = math.sqrt(h["ts2"]), math.sqrt(h["tu2"])
        c = h["kap"] * ts * tu
        return np.array([[h["ts2"], c], [c, h["tu2"]]])

    # ----------------------------------------------------------- team priors
    def _carry_total(self, team: TeamKey, m: np.ndarray, s: Year) -> Tuple[float, int]:
        """New-season prior mean of the total strength (s + u) of a team last seen in s.

        The last-season total is blended with the mean of up to ``hist_k`` older seasons
        and multiplied by rho per season of gap. Returns (mean total, gap).
        """
        c = self.cfg
        gap = max(1, int(self.season - s)) if self.season is not None else 1
        T = float(m.sum())
        older = [x for (ss, x) in self.hist.get(team, []) if ss < s][-c.hist_k :]
        if older:
            T = (1.0 - c.hist_beta) * T + c.hist_beta * (sum(older) / len(older))
        return c.rho**gap * T, gap

    def _get_ev_pcg(self, event_key: EventKey) -> EventPCG:
        st = self.ev_pcg.get(event_key)
        if st is None:
            st = ({}, {}, {})
            self.ev_pcg[event_key] = st
        return st

    def _team_latest_pcg_z(self, team: TeamKey, event_key: EventKey, h: Hyper) -> float:
        """The most recent per-event PCG rating of ``team``."""
        st = self.ev_pcg.get(event_key)
        if st is not None and team in st[2]:
            return st[2][team]
        evs = self.team_events.get(team)
        if evs:
            for prev_ek in reversed(evs):
                pst = self.ev_pcg.get(prev_ek)
                if pst is not None and team in pst[2]:
                    return pst[2][team]
        return self._prior_z_scalar(team, h)

    def _solve_event_pcg(self, ek: EventKey, reg: float) -> None:
        """Solve the clamped subgraph normal equations for the active teams of ``ek``."""
        e_ata, e_atb, e_z = self._get_ev_pcg(ek)
        active = set(e_atb.keys())
        sub_ata: Dict[TeamKey, Dict[TeamKey, float]] = {}
        sub_atb: Dict[TeamKey, float] = {}
        # Sorted, so that the solve does not depend on the string hash seed.
        for t in sorted(active):
            b_t = reg * self.team_z0[t]
            row_t: Dict[TeamKey, float] = {}
            for ev_k in self.team_events.get(t, ()):
                pst = self.ev_pcg.get(ev_k)
                if pst is None or t not in pst[1]:
                    continue
                b_t += pst[1][t]
                for u, w_tu in pst[0][t].items():
                    if u in active:
                        row_t[u] = row_t.get(u, 0.0) + w_tu
                    else:
                        z_u = pst[2].get(u, self.team_z0.get(u, 0.0))
                        b_t -= w_tu * z_u
            sub_ata[t] = row_t
            sub_atb[t] = b_t
        new_z = _solve_pcg_dict(sub_ata, sub_atb, reg, e_z, iters=5)
        e_z.clear()
        e_z.update(new_z)
        self.pcg_z.update(new_z)

    def _global_prior(
        self, team: TeamKey, event_key: EventKey, h: Hyper
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prior mean and covariance of a team that enters an event state."""
        c = self.cfg
        S0 = self._prior_cov(h)
        g = S0 @ np.ones(2)
        tT2 = float(g.sum())
        st = self.teams.get(team)
        if st is None:
            m = np.asarray(c.rookie_z * math.sqrt(tT2) * g / tT2)
            return m, S0.copy()
        m, P, s, ev = st
        if s != self.season:
            carried, gap = self._carry_total(team, m, s)
            rv = c.rho_v**gap
            vT = float(P.sum())
            mean = np.asarray(carried * g / tT2)
            explained = rv * rv * max(tT2 - vT, 0.0)
            explained = min(explained, 0.98 * tT2)
            Pn = S0 - np.outer(g, g) * explained / (tT2 * tT2)
            return mean, Pn
        if ev != event_key:
            w = g / tT2
            m_new = m + c.drift_event * w
            pst = self.ev_pcg.get(ev)
            if pst is not None and team in pst[2]:
                diff = pst[2][team] - float(m.sum())
                m_new = m_new + c.pcg_ev_carry * diff * w
            return m_new, P + c.q_event * S0
        return m, P

    def _view(
        self, event_key: EventKey, teams: Sequence[TeamKey], h: Hyper
    ) -> Tuple[np.ndarray, np.ndarray]:
        es = self.events.get(event_key)
        k = len(teams)
        mu = np.zeros(2 * k)
        cov = np.zeros((2 * k, 2 * k))
        inside_a: List[int] = []
        inside_i: List[int] = []
        for a, t in enumerate(teams):
            if es is not None and t in es.idx:
                i = es.idx[t]
                inside_a += [2 * a, 2 * a + 1]
                inside_i += [i, i + 1]
            else:
                m, P = self._global_prior(t, event_key, h)
                mu[2 * a : 2 * a + 2] = m
                cov[2 * a : 2 * a + 2, 2 * a : 2 * a + 2] = P
        if es is not None and inside_a:
            mu[inside_a] = es.mu[inside_i]
            cov[np.ix_(inside_a, inside_a)] = es.cov[np.ix_(inside_i, inside_i)]
        return mu, cov

    # ------------------------------------------------------------ interface
    def _level_parts(self, n_red: int) -> float:
        """Expected alliance score for an average alliance of n_red robots (points)."""
        if self.n == 0:
            return self._mean_total()
        if self.comp:
            return self.Ls + n_red * self.Lu + self.foul.mean
        return self.Ls

    def _shape_init(self) -> None:
        B, w = SHAPE_SUPPORT, MARGIN_BIN_W
        nb = int(round(2 * B / w))
        edges = np.linspace(-B, B, nb + 1)
        cdf = np.array([_phi(x) for x in edges])
        cdf[0], cdf[-1] = 0.0, 1.0
        self.sh_norm: np.ndarray = np.diff(cdf)  # normal prior mass per bin
        self.sh_pool: np.ndarray = np.zeros(nb)  # past seasons (normalized counts)
        self.sh_pool_n = 0.0
        self.sh_cur: np.ndarray = np.zeros(nb)  # current season counts
        self.sh_cur_n = 0.0
        self.sh_mass: np.ndarray = np.zeros(nb)
        self.sh_cum: np.ndarray = np.zeros(nb + 1)
        self._shape_refresh()

    def _shape_add(self, t: float) -> None:
        B, w = SHAPE_SUPPORT, MARGIN_BIN_W
        nb = len(self.sh_cur)
        i = int((min(max(t, -B + 1e-9), B - 1e-9) + B) / w)
        i = min(max(i, 0), nb - 1)
        self.sh_cur[i] += 0.5
        self.sh_cur[nb - 1 - i] += 0.5
        self.sh_cur_n += 1.0
        self._shape_refresh()

    def _shape_roll(self) -> None:
        """Merge the finished season into the pooled margin shape."""
        if self.sh_cur_n > 0:
            self.sh_pool += self.sh_cur
            self.sh_pool_n += self.sh_cur_n
        self.sh_cur = np.zeros(len(self.sh_cur))
        self.sh_cur_n = 0.0
        self._shape_refresh()

    def _shape_refresh(self) -> None:
        mass = self.cfg.shape_kn * self.sh_norm + self.sh_cur
        if self.sh_pool_n > 0:
            mass = mass + self.cfg.shape_kp * self.sh_pool / self.sh_pool_n
        mass = mass / mass.sum()
        self.sh_mass = mass
        self.sh_cum = np.concatenate(([0.0], np.cumsum(mass)))

    def _win_prob(self, x: float) -> float:
        if x > 0:
            return 1.0 - self._win_prob(-x)
        B, w = SHAPE_SUPPORT, MARGIN_BIN_W
        if x <= -B:
            return 0.0
        pos = (x + B) / w
        i = min(int(pos), len(self.sh_mass) - 1)
        return float(self.sh_cum[i] + (pos - i) * self.sh_mass[i])

    def _wr_get(self, team: TeamKey) -> float:
        return self.wr.get(team, 0.0)

    def _wr_diff(self, red: Sequence[TeamKey], blue: Sequence[TeamKey]) -> float:
        return sum((self._wr_get(t) for t in red), 0.0) - sum(
            (self._wr_get(t) for t in blue), 0.0
        )

    def _prior_z_scalar(self, team: TeamKey, h: Hyper) -> float:
        """Scalar total strength (s + u) of a team from the causal state.

        It is the in-season filter total if the team already played this season, else the
        carried-over new-season prior mean (rookie prior for an unseen team).
        """
        S0 = self._prior_cov(h)
        tT2 = float((S0 @ np.ones(2)).sum())
        st = self.teams.get(team)
        if st is None:
            return self.cfg.rookie_z * math.sqrt(max(tT2, 1e-6))
        m, _, s, _ = st
        if s == self.season:
            return float(m.sum())
        return self._carry_total(team, m, s)[0]

    def _pcg_diff_res(
        self,
        red: Sequence[TeamKey],
        blue: Sequence[TeamKey],
        feats: Tuple[float, ...],
        h: Hyper,
        event_key: EventKey,
    ) -> float:
        """Cross-event PCG rating difference minus local filter total-strength difference."""
        if not self.team_events:
            return 0.0
        pr = sum((self._team_latest_pcg_z(t, event_key, h) for t in red), 0.0)
        pb = sum((self._team_latest_pcg_z(t, event_key, h) for t in blue), 0.0)
        tz_diff = (feats[0] + feats[1]) - (feats[2] + feats[3])
        return (pr - pb) - tz_diff

    def _final_prob(
        self,
        p_h: float,
        red: Sequence[TeamKey],
        blue: Sequence[TeamKey],
        event_key: EventKey,
        feats: Tuple[float, ...],
        h: Hyper,
        zs: Tuple[float, float],
        is_qual: bool,
    ) -> Tuple[float, np.ndarray]:
        """Stacked win probability and the stacker feature vector.

        Every feature is antisymmetric under a red/blue swap, so the stacker (no intercept)
        keeps p(red) = 1 - p(blue). Features: [filter logit, win rating, rank (2), events
        played, predictive variance, cross-event residual, logit times score level, DQ
        rates, three playoff interactions].
        """
        c = self.cfg
        pc = min(max(p_h, 1e-6), 1.0 - 1e-6)
        lf, wd = math.log(pc / (1.0 - pc)), self._wr_diff(red, blue)
        x = np.array([lf, wd])
        rank = feats[6:8]
        x = np.concatenate([x, np.asarray(rank, dtype=float)])
        x = np.append(x, self._nev(red, event_key) - self._nev(blue, event_key))
        x = np.append(x, float(feats[4] - feats[5]))
        pcg_r = self._pcg_diff_res(red, blue, feats, h, event_key)
        x = np.append(x, pcg_r)
        # Count noise grows with the expected score, so the same strength gap is less
        # decisive in a high-scoring match. S is the mean expected alliance z above the
        # season level, saturated above 0.
        S = 0.5 * (zs[0] + zs[1])
        if S > 0.0:
            s0 = c.stack_lvl_s0_qm if is_qual else c.stack_lvl_s0_po
            S = S / (1.0 + S / max(s0, 1e-6))
        x = np.append(x, lf * S)
        # A DQ marks a team whose later output is below its filter estimate. The feature
        # harmed playoff Brier, so it is 0 in playoffs.
        x = np.append(x, self._dq_feat(red, blue) if is_qual else 0.0)
        is_po = 0.0 if is_qual else 1.0
        rb_diff = float(rank[1])
        u_diff = float(feats[1] - feats[3])
        x = np.concatenate(
            [x, np.array([is_po * rb_diff, is_po * u_diff, is_po * pcg_r])]
        )
        return self.stacker.prob(x), x

    def _dq_feat(self, red: Sequence[TeamKey], blue: Sequence[TeamKey]) -> float:
        """Red - blue sum of shrunk team DQ rates, in units of 0.05."""
        k, r0 = self.cfg.dq_k, self.cfg.dq_r0

        def tot(teams: Sequence[TeamKey]) -> float:
            out = 0.0
            for t in teams:
                d, c = self.dq_t.get(t, (0.0, 0.0))
                out += (d + k * r0) / (c + k)
            return out

        return (tot(red) - tot(blue)) / 0.05

    def _nev(self, teams: Sequence[TeamKey], event_key: EventKey) -> float:
        """Sum over the teams of the number of earlier events this season."""
        tot = 0
        for t in teams:
            nv = self.nevc.get(t)
            if nv is not None:
                tot += nv[0] if nv[1] == event_key else nv[0] + 1
        return float(tot)

    def _foul_adj(self, opp: Sequence[TeamKey]) -> float:
        """Expected foul points above the season mean that the opponents give (points)."""
        if not self.comp:
            return 0.0
        k = self.cfg.foul_k
        tot = 0.0
        for t in opp:
            sm, n = self.fteam.get(t, (0.0, 0.0))
            tot += sm / (n + k)
        return tot

    def _bucket(self, x: float, is_qual: bool) -> ShapeKey:
        """Shape bucket of a residual with standardized score level x."""
        lo, hi = LEVEL_EDGES
        xk = 0 if x < lo else (2 if x > hi else 1)
        return (xk, bool(is_qual))

    def _forecast_bucket(self, x: float, is_qual: bool) -> Optional[ShapeKey]:
        """Shape bucket of a forecast, or None for the global shape during the first
        ``gmm_cond_guard`` matches of the season (``self.n`` counts alliances)."""
        if self.n < 2 * self.cfg.gmm_cond_guard:
            return None
        return self._bucket(x, is_qual)

    def _score_emp_probs(
        self, mean: float, sd: float, key: Optional[ShapeKey]
    ) -> np.ndarray:
        """Probabilities on integers >= 0 of mean + sd * T with the learned shape of T."""
        sd = max(sd, 0.5)
        B = SHAPE_SUPPORT
        hi = int(math.ceil(max(mean, 0.0) + B * sd)) + 1
        z = (np.arange(hi + 1) + 0.5 - mean) / sd
        cdf = (self.gmm_b[key] if key is not None else self.gmm).cdf(z)
        probs = np.diff(np.concatenate(([0.0], cdf)))
        probs[-1] += 1.0 - cdf[-1]
        probs = np.clip(probs, 0.0, None)
        return probs / probs.sum()

    def _struct_arms(
        self,
        mean: float,
        sd: float,
        teams: Sequence[TeamKey],
        is_po: bool,
        key: Optional[ShapeKey],
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """(base, stepped) PMFs of one alliance. The stepped PMF is None before the
        component model is ready."""
        pe = self._score_emp_probs(mean, sd, key)
        return pe, self.struct.arms(pe, teams, is_po, mean, sd)

    def _score_cal_shift(self, x: float) -> float:
        """Calibrated mean shift in sigma units for a standardized deviation x."""
        n, sx, sxx, se, sxe = self.sc
        ka, kc = self.cfg.score_cal_ka, self.cfg.score_cal_kc
        A = np.array([[n + ka, sx], [sx, sxx + kc]])
        a, c = np.linalg.solve(A, np.array([se, sxe]))
        return float(a + c * x)

    def _var_mult(self, x: float) -> float:
        """PMF sd multiplier sqrt(c0 + c1 x) for a standardized mean deviation x."""
        n, sx, sxx, sq, sxq = self.vc
        k = self.cfg.var_cal_k
        A = np.array([[n + k, sx], [sx, sxx + k]])
        c0, c1 = np.linalg.solve(A, np.array([sq + k, sxq]))
        return math.sqrt(max(float(c0 + c1 * x), self.cfg.var_cal_floor))

    def _rp_keys(self) -> Tuple[str, ...]:
        if self.season is None or self.season < 2016:
            return ()
        return ("rp_1", "rp_2", "rp_3") if self.season >= 2025 else ("rp_1", "rp_2")

    def _rp_x(
        self,
        feats: Tuple[float, ...],
        nr: int,
        nb: int,
        po: Tuple[float, float],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Bonus RP features per alliance: [1, own shared, own robot, opponent total] / sigma.

        ``po`` holds the event-progress offsets (points) of red and blue, which shift the
        shared parts.
        """
        sr, ur, sb, ub = feats[:4]
        sig = max(self._sigma(), 1e-6)
        gam = self._gamma()
        pr, pb = po[0] / sig, po[1] / sig
        if self.comp and self.n > 0:
            ls, lu, lf = self.Ls / sig, self.Lu / sig, self.foul.mean / sig
            s_red, s_blue = ls + sr - gam * sb + pr, ls + sb - gam * sr + pb
            u_red, u_blue = nr * lu + ur, nb * lu + ub
            t_red, t_blue = s_red + u_red + lf, s_blue + u_blue + lf
        else:
            lvl = self._level_parts(nr) / sig
            s_red = lvl + sr + ur - gam * sb + pr
            s_blue = lvl + sb + ub - gam * sr + pb
            u_red = u_blue = 0.0
            t_red, t_blue = s_red, s_blue
        return (
            np.array([1.0, s_red, u_red, t_blue]),
            np.array([1.0, s_blue, u_blue, t_red]),
        )

    @staticmethod
    def _rp_x_rank(
        x_r: np.ndarray, x_b: np.ndarray, feats: Tuple[float, ...]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Append the own-alliance rank features (top and bottom minus mean)."""
        return np.concatenate([x_r, feats[8:10]]), np.concatenate([x_b, feats[10:12]])

    def _rb_z_map(self, teams: Sequence[TeamKey], h: Hyper) -> Dict[TeamKey, float]:
        """Standardized team skill for the cold start of the rulebook channels."""
        S0 = self._prior_cov(h)
        sd0 = math.sqrt(max(float((S0 @ np.ones(2)).sum()), 1e-6))
        return {t: self._prior_z_scalar(t, h) / sd0 for t in teams}

    def _rp_bonus(
        self,
        keys: Sequence[str],
        x: np.ndarray,
        tier: str,
        teams: Sequence[TeamKey],
        opp: Sequence[TeamKey],
    ) -> Dict[str, float]:
        """Bonus RP probabilities per key: the rulebook model, else the logistic fallback."""
        bon = self.bonus.probs(keys, x[:4])
        if self.rbonus.supported():
            z_map = self._rb_z_map(list(teams) + list(opp), self._hyper())
            rule = self.rbonus.probs(keys, tier, teams, opp, x[1:], z_map)
            out: Dict[str, float] = {}
            for k in keys:
                rk = rule.get(k)
                out[k] = bon[k] if rk is None else rk
            return out
        return bon

    def _rp_pred(
        self,
        p_win: float,
        x: np.ndarray,
        tier: str,
        teams: Sequence[TeamKey],
        opp: Sequence[TeamKey],
    ) -> Optional[RankingPointsPrediction]:
        keys = self._rp_keys()
        season = self.season
        if not keys or season is None:
            return None
        bon = self._rp_bonus(keys, x, tier, teams, opp)
        wv, tv = rp_values(season)
        max_rp = float(wv + len(keys))
        # p_win counts a tie as half a win: P(W) = p - P(T)/2. The mean RP is
        # wv P(W) + tv P(T) + sum q = wv p + (tv - wv/2) P(T) + sum q.
        pw, pt, _ = self.rpj.outcome_probs(p_win)
        exp = min(
            max_rp, max(0.0, wv * p_win + (tv - 0.5 * wv) * pt + sum(bon.values()))
        )
        median = RPJoint.median(self.rpj.pmf(p_win, bon, wv, tv))
        return RankingPointsPrediction(
            expected_rp=exp,
            win_rp_prob=min(1.0, max(0.0, pw)),
            bonus_rp_probs=bon,
            max_rp=max_rp,
            median_rp=median,
        )

    # ------------------------------------------------------ rank aggregation
    def _agg_coef(self) -> np.ndarray:
        """Per-season rank weights [own top, own bottom, opp top, opp bottom] (ridge)."""
        k = self.cfg.agg_k
        A = self.ag_xx + k * np.eye(4)
        return np.linalg.solve(A, self.ag_xe + k * self.ag_prior)

    @staticmethod
    def _rank_x(s: np.ndarray, t: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """Centered top and bottom shared strengths, ranked by total strength t."""
        n = len(s)
        if n < 2:
            return np.zeros(2), 0, 0
        order = np.argsort(-t, kind="stable")
        i_top, i_bot = int(order[0]), int(order[-1])
        sm = float(s.mean())
        return np.array([s[i_top] - sm, s[i_bot] - sm]), i_top, i_bot

    def _agg_w(
        self, s: np.ndarray, t: np.ndarray, a_top: float, a_bot: float
    ) -> np.ndarray:
        """Weights 1 + a_top (1[top] - 1/n) + a_bot (1[bot] - 1/n) on one alliance."""
        n = len(s)
        w = np.ones(n)
        if n < 2 or (a_top == 0.0 and a_bot == 0.0):
            return w
        _, i_top, i_bot = self._rank_x(s, t)
        w -= (a_top + a_bot) / n
        w[i_top] += a_top
        w[i_bot] += a_bot
        return w

    def _alliance_rows(
        self, mu: np.ndarray, nr: int, nb: int, gam: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Linear rows of the red and blue score z over [s, u] per team (red teams first)."""
        k = nr + nb
        wr = np.zeros(2 * k)
        wb = np.zeros(2 * k)
        wr[: 2 * nr] = 1.0
        wb[2 * nr :] = 1.0
        wr[2 * nr :: 2] -= gam
        wb[0 : 2 * nr : 2] -= gam
        a = self._agg_coef()
        s_r, s_b = mu[0 : 2 * nr : 2], mu[2 * nr :: 2]
        t_r = s_r + mu[1 : 2 * nr : 2]
        t_b = s_b + mu[2 * nr + 1 :: 2]
        wr[0 : 2 * nr : 2] = self._agg_w(s_r, t_r, a[0], a[1])
        wb[2 * nr :: 2] = self._agg_w(s_b, t_b, a[0], a[1])
        wr[2 * nr :: 2] = self._agg_w(s_b, t_b, a[2], a[3]) - 1.0 - gam
        wb[0 : 2 * nr : 2] = self._agg_w(s_r, t_r, a[2], a[3]) - 1.0 - gam
        return wr, wb

    @staticmethod
    def _rank_feats(mu: np.ndarray, nr: int) -> np.ndarray:
        """Stacker rank features: red minus blue [top, bottom] total strength."""
        t = mu[0::2] + mu[1::2]
        tr, tb = np.sort(t[:nr]), np.sort(t[nr:])
        if len(tr) == 0 or len(tb) == 0:
            return np.zeros(2)
        return np.array([tr[-1] - tb[-1], tr[0] - tb[0]])

    @staticmethod
    def _own_rank(mu: np.ndarray, nr: int) -> np.ndarray:
        """[red top - mean, red bottom - mean, blue top - mean, blue bottom - mean]."""
        t = mu[0::2] + mu[1::2]
        out = np.zeros(4)
        for j, a in enumerate((t[:nr], t[nr:])):
            if len(a) >= 2:
                out[2 * j] = float(a.max() - a.mean())
                out[2 * j + 1] = float(a.min() - a.mean())
        return out

    @staticmethod
    def _sorted_s(mu: np.ndarray, nr: int) -> np.ndarray:
        """Shared strengths sorted by descending total strength for 3-team alliances."""
        s = mu[0::2]
        t = s + mu[1::2]
        out = np.zeros(6)
        for j, (s_a, t_a) in enumerate(((s[:nr], t[:nr]), (s[nr:], t[nr:]))):
            if len(s_a) == 3:
                ord_i = np.argsort(-t_a, kind="stable")
                out[3 * j : 3 * j + 3] = s_a[ord_i]
        return out

    def _refresh_sat_w(self) -> None:
        """Online ridge weights of the playoff (0:2) and rank (2:6) score calibrations."""
        A = self.sat_xx_pool + self.sat_xx_cur + self.cfg.sat_k * np.eye(SAT_DIM)
        b = self.sat_xe_pool + self.sat_xe_cur
        self.sat_w = np.linalg.solve(A, b)

    def _sat_feats(
        self,
        ek: EventKey,
        teams: Sequence[TeamKey],
        s_ord: Sequence[float],
        z_opp: float,
        is_qual: bool,
    ) -> np.ndarray:
        """Alliance score saturation features in sigma units: playoff progression and
        defense, and multi-elite sub-additivity of 3-team alliances."""
        x = np.zeros(SAT_DIM)
        if not is_qual:
            h_po = self.po_res.get((ek, tuple(sorted(teams))))
            po_len = float(len(h_po)) if h_po else 0.0
            x[0] = min(po_len, 6.0) / 6.0
            x[1] = max(0.0, z_opp)
        if len(teams) == 3:
            s1, s2, s3 = float(s_ord[0]), float(s_ord[1]), float(s_ord[2])
            s12 = max(0.0, s1) * max(0.0, s2)
            x[2] = s1 - self.qm_s_mean[0]
            x[3] = s2 - self.qm_s_mean[1]
            x[4] = s3 - self.qm_s_mean[2]
            x[5] = s12 - self.qm_s_mean[3]
        return x

    def _margin(
        self,
        red: Sequence[TeamKey],
        blue: Sequence[TeamKey],
        event_key: EventKey,
        h: Hyper,
    ) -> Tuple[float, float, float, float, Tuple[float, ...]]:
        """(mean margin, margin variance, red z, blue z, features) in sigma units.

        Features: sum s red, sum u red, sum s blue, sum u blue, red and blue predictive
        variances, rank features (2), own-rank features (4), sorted shared strengths (6).
        """
        mu, cov = self._view(event_key, list(red) + list(blue), h)
        nr, nb = len(red), len(blue)
        gam = self._gamma()
        # red score z = sum(s+u)_red - gam * sum(s)_blue, and likewise for blue.
        wr, wb = self._alliance_rows(mu, nr, nb, gam)
        hv = wr - wb
        # Foul transfer moves the alliance score means only, not the margin.
        fa_r, fa_b = self._foul_adj(blue), self._foul_adj(red)
        d = float(hv @ mu)
        noise = (
            2.0 * h["rs"] * (1.0 - self.cfg.noise_corr)
            + (nr + nb) * h["ru"]
            + 2.0 * h["rf"]
        )
        var = float(hv @ cov @ hv) + noise
        zr_ = float(wr @ mu) + fa_r / self._sigma()
        zb_ = float(wb @ mu) + fa_b / self._sigma()
        own_noise_r = h["rs"] + nr * h["ru"] + h["rf"]
        own_noise_b = h["rs"] + nb * h["ru"] + h["rf"]
        feats = (
            (
                float(mu[0 : 2 * nr : 2].sum()),
                float(mu[1 : 2 * nr : 2].sum()),
                float(mu[2 * nr :: 2].sum()),
                float(mu[2 * nr + 1 :: 2].sum()),
                float(wr @ cov @ wr) + own_noise_r,
                float(wb @ cov @ wb) + own_noise_b,
            )
            + tuple(float(v) for v in self._rank_feats(mu, nr))
            + tuple(float(v) for v in self._own_rank(mu, nr))
            + tuple(float(v) for v in self._sorted_s(mu, nr))
        )
        return d, var, zr_, zb_, feats

    def _playoff_bonus_forecast(
        self,
        red: Sequence[TeamKey],
        blue: Sequence[TeamKey],
        feats: Tuple[float, ...],
        po: Tuple[float, float],
        event_key: EventKey,
        event_type: EventType,
    ) -> Tuple[float, float, float, float]:
        """Expected 2016/2017 playoff threshold bonus points and variances (red, blue)."""
        if self.season not in (2016, 2017):
            return 0.0, 0.0, 0.0, 0.0
        x_r, x_b = self._rp_x_rank(*self._rp_x(feats, len(red), len(blue), po), feats)
        tier = tier_of(event_key, event_type)
        bon_r = self._rp_bonus(("rp_1", "rp_2"), x_r, tier, red, blue)
        bon_b = self._rp_bonus(("rp_1", "rp_2"), x_b, tier, blue, red)
        w1, w2 = (20.0, 25.0) if self.season == 2016 else (20.0, 100.0)
        p1_r, p2_r = bon_r["rp_1"], bon_r["rp_2"]
        p1_b, p2_b = bon_b["rp_1"], bon_b["rp_2"]
        eb_r = w1 * p1_r + w2 * p2_r
        eb_b = w1 * p1_b + w2 * p2_b
        eb_vr = w1 * w1 * p1_r * (1.0 - p1_r) + w2 * w2 * p2_r * (1.0 - p2_r)
        eb_vb = w1 * w1 * p1_b * (1.0 - p1_b) + w2 * w2 * p2_b * (1.0 - p2_b)
        return eb_r, eb_b, eb_vr, eb_vb

    def _po_synergy(
        self,
        event_key: EventKey,
        red: Sequence[TeamKey],
        blue: Sequence[TeamKey],
        is_qual: bool,
    ) -> Tuple[float, float]:
        """Shrunk pre-match standardized playoff residual of the fixed alliances."""
        if is_qual:
            return 0.0, 0.0
        k = self.cfg.po_syn_k
        hr = self.po_res.get((event_key, tuple(sorted(red))))
        hb = self.po_res.get((event_key, tuple(sorted(blue))))
        sr = float(sum(hr)) / (len(hr) + k) if hr else 0.0
        sb = float(sum(hb)) / (len(hb) + k) if hb else 0.0
        return sr, sb

    def _score_ms(
        self,
        red: Sequence[TeamKey],
        blue: Sequence[TeamKey],
        ek: EventKey,
        is_qual: bool,
        sig: float,
        feats: Tuple[float, ...],
        zr: float,
        zb: float,
        po: Tuple[float, float],
        eb: Tuple[float, float],
        eb_v: Tuple[float, float],
        sy: Tuple[float, float],
    ) -> Tuple[float, float, float, float]:
        """Score PMF means and sds (mr, mb, sd_r, sd_b) of both alliances. Read-only."""
        c = self.cfg
        mr = self._level_parts(len(red)) + sig * zr + eb[0]
        mb = self._level_parts(len(blue)) + sig * zb + eb[1]
        mr += sig * self._score_cal_shift(zr)
        mb += sig * self._score_cal_shift(zb)
        mr += po[0] + sig * c.po_syn_s * sy[0]
        mb += po[1] + sig * c.po_syn_s * sy[1]
        mr += sig * float(
            self.sat_w @ self._sat_feats(ek, red, feats[12:15], zb, is_qual)
        )
        mb += sig * float(
            self.sat_w @ self._sat_feats(ek, blue, feats[15:18], zr, is_qual)
        )
        rr = self._pmf_scale()
        sd_r = (
            rr
            * sig
            * math.sqrt(max(feats[4], 1e-9))
            * self._var_mult((mr - eb[0] - self._level_parts(len(red))) / sig)
        )
        sd_b = (
            rr
            * sig
            * math.sqrt(max(feats[5], 1e-9))
            * self._var_mult((mb - eb[1] - self._level_parts(len(blue))) / sig)
        )
        if eb_v[0] > 0.0 or eb_v[1] > 0.0:
            sd_r = math.hypot(sd_r, math.sqrt(eb_v[0]))
            sd_b = math.hypot(sd_b, math.sqrt(eb_v[1]))
        return mr, mb, sd_r, sd_b

    def predict_match(self, context: MatchContext) -> MatchPrediction:
        """Forecast one match from the current state. The method does not change state."""
        red = list(context.red_teams)
        blue = list(context.blue_teams)
        ek = context.event_key
        h = self._hyper()
        d, var, zr, zb, feats = self._margin(red, blue, ek, h)
        sig = self._sigma()
        is_qual = context.is_qual
        po_r, po_b = self._prog_off(ek, red), self._prog_off(ek, blue)
        eb_r = eb_b = 0.0
        eb_vr = eb_vb = 0.0
        if not is_qual and self.season in (2016, 2017):
            eb_r, eb_b, eb_vr, eb_vb = self._playoff_bonus_forecast(
                red, blue, feats, (po_r, po_b), ek, context.event_type
            )
            d += (eb_r - eb_b) / sig
            var += (eb_vr + eb_vb) / (sig * sig)
        sy_r, sy_b = self._po_synergy(ek, red, blue, is_qual)
        d += self.cfg.po_syn_d * (sy_r - sy_b)
        p, _ = self._final_prob(
            self._win_prob(d / math.sqrt(max(var, 1e-9))),
            red,
            blue,
            ek,
            feats,
            h,
            (zr, zb),
            is_qual,
        )
        p = min(1.0, max(0.0, p))
        mr, mb, sd_r, sd_b = self._score_ms(
            red,
            blue,
            ek,
            is_qual,
            sig,
            feats,
            zr,
            zb,
            (po_r, po_b),
            (eb_r, eb_b),
            (eb_vr, eb_vb),
            (sy_r, sy_b),
        )
        kr = self._forecast_bucket(
            (mr - eb_r - self._level_parts(len(red))) / sig, is_qual
        )
        kb = self._forecast_bucket(
            (mb - eb_b - self._level_parts(len(blue))) / sig, is_qual
        )
        red_score = ScoreDistribution(
            self.struct.mix(*self._struct_arms(mr, sd_r, red, not is_qual, kr))
        )
        blue_score = ScoreDistribution(
            self.struct.mix(*self._struct_arms(mb, sd_b, blue, not is_qual, kb))
        )
        red_rp = blue_rp = None
        if is_qual:
            x_r, x_b = self._rp_x_rank(
                *self._rp_x(feats, len(red), len(blue), (po_r, po_b)), feats
            )
            tier = tier_of(ek, context.event_type)
            red_rp = self._rp_pred(p, x_r, tier, red, blue)
            blue_rp = self._rp_pred(1.0 - p, x_b, tier, blue, red)
        return MatchPrediction(
            red_win_prob=p,
            red_score=red_score,
            blue_score=blue_score,
            red_rp=red_rp,
            blue_rp=blue_rp,
        )

    def update(self, context: MatchContext, outcome: MatchOutcome) -> None:
        """Learn from one played match. Every learner trains on the pre-match inputs."""
        c = self.cfg
        red = list(context.red_teams)
        blue = list(context.blue_teams)
        if not red or not blue or self.season is None:
            return
        season = self.season
        h = self._hyper()
        sig = self._sigma()
        ek = context.event_key
        is_qual = context.is_qual
        ev_type = context.event_type
        # Pre-update forecast quantities. Compute them all before any state changes so
        # that every online learner trains on the same inputs predict_match used.
        d, var, zr, zb, feats = self._margin(red, blue, ek, h)
        pre_po = (self._prog_off(ek, red), self._prog_off(ek, blue))
        pre_pb = (self._prog_bin(ek, red), self._prog_bin(ek, blue))
        eb_r = eb_b = 0.0
        eb_vr = eb_vb = 0.0
        if not is_qual and season in (2016, 2017):
            eb_r, eb_b, eb_vr, eb_vb = self._playoff_bonus_forecast(
                red, blue, feats, pre_po, ek, ev_type
            )
            d += (eb_r - eb_b) / sig
            var += (eb_vr + eb_vb) / (sig * sig)
        pre_sy = self._po_synergy(ek, red, blue, is_qual)
        # Score structure: the (base, stepped) PMFs that predict_match mixed.
        mr_s, mb_s, sdr_s, sdb_s = self._score_ms(
            red,
            blue,
            ek,
            is_qual,
            sig,
            feats,
            zr,
            zb,
            pre_po,
            (eb_r, eb_b),
            (eb_vr, eb_vb),
            pre_sy,
        )
        kr_s = self._forecast_bucket(
            (mr_s - eb_r - self._level_parts(len(red))) / sig, is_qual
        )
        kb_s = self._forecast_bucket(
            (mb_s - eb_b - self._level_parts(len(blue))) / sig, is_qual
        )
        pre_struct = (
            self._struct_arms(mr_s, sdr_s, red, not is_qual, kr_s),
            self._struct_arms(mb_s, sdb_s, blue, not is_qual, kb_s),
        )
        p_h = self._win_prob(d / math.sqrt(max(var, 1e-9)))
        p_pre, x_stack = self._final_prob(
            p_h, red, blue, ek, feats, h, (zr, zb), is_qual
        )
        p_pre = min(1.0, max(0.0, p_pre))
        x_rp_red, x_rp_blue = self._rp_x_rank(
            *self._rp_x(feats, len(red), len(blue), pre_po), feats
        )
        rp_keys = self._rp_keys()
        tier = tier_of(ek, ev_type)
        pre_bon: Optional[Tuple[Dict[str, float], Dict[str, float]]] = None
        if rp_keys and is_qual:
            # Pre-update bonus probabilities, as in predict_match. The joint RP model (tie
            # rate and rho) trains on them.
            pre_bon = (
                self._rp_bonus(rp_keys, x_rp_red, tier, red, blue),
                self._rp_bonus(rp_keys, x_rp_blue, tier, blue, red),
            )
        bd_red, bd_blue = outcome.red_breakdown, outcome.blue_breakdown
        pb_r = playoff_bonus_points(season, bd_red, is_qual)
        pb_b = playoff_bonus_points(season, bd_blue, is_qual)
        rsc_clean = float(outcome.red_score) - pb_r
        bsc_clean = float(outcome.blue_score) - pb_b
        e_m = (float(outcome.red_score) - float(outcome.blue_score)) / sig - d
        y_win = float(outcome.red_win)

        if self.n > 0:
            self._shape_add(e_m / math.sqrt(max(var, 1e-9)))
        pre_shift = (self._score_cal_shift(zr), self._score_cal_shift(zb))
        x_sat_r = self._sat_feats(ek, red, feats[12:15], zb, is_qual)
        x_sat_b = self._sat_feats(ek, blue, feats[15:18], zr, is_qual)
        pre_sat = (float(self.sat_w @ x_sat_r), float(self.sat_w @ x_sat_b))
        if self.n > 0:
            base_r = (
                self._level_parts(len(red))
                + sig * (zr + pre_shift[0])
                + pre_po[0]
                + sig * c.po_syn_s * pre_sy[0]
            )
            base_b = (
                self._level_parts(len(blue))
                + sig * (zb + pre_shift[1])
                + pre_po[1]
                + sig * c.po_syn_s * pre_sy[1]
            )
            delta_sat = c.sat_huber
            for x_s, pred_s, y_s, b_s in (
                (x_sat_r, pre_sat[0], rsc_clean, base_r),
                (x_sat_b, pre_sat[1], bsc_clean, base_b),
            ):
                if np.any(x_s != 0.0):
                    e_s = (float(y_s) - b_s) / sig
                    res_clip = max(-delta_sat, min(delta_sat, e_s - pred_s))
                    self.sat_xx_cur += np.outer(x_s, x_s)
                    self.sat_xe_cur += x_s * (pred_s + res_clip)
            self._refresh_sat_w()
        if is_qual and len(red) == 3 and len(blue) == 3:
            for sr_s in (feats[12:15], feats[15:18]):
                vec = np.array(
                    [sr_s[0], sr_s[1], sr_s[2], max(0.0, sr_s[0]) * max(0.0, sr_s[1])]
                )
                self.qm_s_n += 1.0
                w_qm = max(1.0 / self.qm_s_n, 1.0 / 2000.0)
                self.qm_s_mean += w_qm * (vec - self.qm_s_mean)
        if not is_qual:
            mr_base = (
                self._level_parts(len(red))
                + sig * (zr + pre_shift[0])
                + pre_po[0]
                + eb_r
            )
            self.po_res.setdefault((ek, tuple(sorted(red))), []).append(
                (float(outcome.red_score) - mr_base) / sig
            )
            mb_base = (
                self._level_parts(len(blue))
                + sig * (zb + pre_shift[1])
                + pre_po[1]
                + eb_b
            )
            self.po_res.setdefault((ek, tuple(sorted(blue))), []).append(
                (float(outcome.blue_score) - mb_base) / sig
            )
        # Pre-update variance multipliers (x = standardized deviation of the score mean).
        pre_x = (
            zr + pre_shift[0] + pre_po[0] / sig,
            zb + pre_shift[1] + pre_po[1] / sig,
        )
        pre_vm = (self._var_mult(pre_x[0]), self._var_mult(pre_x[1]))
        pre_rr = self._pmf_scale()
        if self.n > 0:
            for z_a, v_a, n_a, y_a, shift, po, x_a, vm_a in (
                (
                    zr,
                    feats[4],
                    len(red),
                    rsc_clean,
                    pre_shift[0],
                    pre_po[0],
                    pre_x[0],
                    pre_vm[0],
                ),
                (
                    zb,
                    feats[5],
                    len(blue),
                    bsc_clean,
                    pre_shift[1],
                    pre_po[1],
                    pre_x[1],
                    pre_vm[1],
                ),
            ):
                m_a = self._level_parts(n_a) + sig * (z_a + shift) + po
                sd_a = pre_rr * sig * math.sqrt(max(v_a, 1e-9))
                t_a = (float(y_a) - m_a) / (sd_a * vm_a)
                self.gmm.add(t_a)
                self.gmm_b[self._bucket(x_a, is_qual)].add(t_a)
                q = ((float(y_a) - m_a) / sd_a) ** 2
                self.vc = c.var_cal_decay * self.vc + np.array(
                    [1.0, x_a, x_a * x_a, q, x_a * q]
                )
                # Fit against the mean of the normal truncated at 0 (close to the PMF mean).
                loc = self._level_parts(n_a) + sig * z_a
                s_a = max(sig * math.sqrt(max(v_a, 1e-9)), 0.5)
                r_ = loc / s_a
                loc = loc * _phi(r_) + s_a * math.exp(-0.5 * r_ * r_) / math.sqrt(
                    2.0 * math.pi
                )
                e_a = (float(y_a) - po - loc) / sig
                self.sc = c.score_cal_decay * self.sc + np.array(
                    [1.0, z_a, z_a * z_a, e_a, z_a * e_a]
                )
            for z_a, n_a, y_a, shift, b in (
                (zr, len(red), rsc_clean, pre_shift[0], pre_pb[0]),
                (zb, len(blue), bsc_clean, pre_shift[1], pre_pb[1]),
            ):
                r_a = float(y_a) - (self._level_parts(n_a) + sig * (z_a + shift))
                self.pg_cur[0, b] += r_a / sig
                self.pg_cur[1, b] += 1.0
        self.struct.learn(
            [
                (pre_struct[0][0], pre_struct[0][1], int(outcome.red_score)),
                (pre_struct[1][0], pre_struct[1][1], int(outcome.blue_score)),
            ]
        )
        self.struct.observe(red, not is_qual, bd_red)
        self.struct.observe(blue, not is_qual, bd_blue)
        self.stacker.update(x_stack, y_win)
        g = c.elo_k * (y_win - 1.0 / (1.0 + math.exp(-x_stack[1])))
        for t in red:
            self.wr[t] = self._wr_get(t) + g
        for t in blue:
            self.wr[t] = self._wr_get(t) - g
        for t in red + blue:
            nv = self.nevc.get(t)
            if nv is None:
                self.nevc[t] = (0, ek)
            elif nv[1] != ek:
                self.nevc[t] = (nv[0] + 1, ek)
            self.scount[t] = self.scount.get(t, 0) + 1
            self.ecount[(ek, t)] = self.ecount.get((ek, t), 0) + 1
        if pre_bon is not None:
            # Train the joint RP PMF on the pre-match forecast: the tie rate once per
            # match, rho_k once per alliance with bonus labels.
            self.rpj.update_tie(p_pre, y_win == 0.5)
            res_red = "W" if y_win == 1.0 else ("L" if y_win == 0.0 else "T")
            res_blue = {"W": "L", "L": "W", "T": "T"}[res_red]
            for p_a, bon_a, res_a, labels in (
                (p_pre, pre_bon[0], res_red, outcome.red_bonus_rps),
                (1.0 - p_pre, pre_bon[1], res_blue, outcome.blue_bonus_rps),
            ):
                if labels:
                    self.rpj.update_bonus(
                        p_a, bon_a, res_a, {k: labels.get(k) for k in rp_keys}
                    )
        if rp_keys and (season in (2016, 2017) or is_qual):
            if is_qual:
                for x_rp, labels in (
                    (x_rp_red, outcome.red_bonus_rps),
                    (x_rp_blue, outcome.blue_bonus_rps),
                ):
                    if labels:
                        self.bonus.update(
                            {k: v for k, v in labels.items() if k in rp_keys}, x_rp[:4]
                        )
            if self.rbonus.supported() and outcome.has_breakdown:
                self.rbonus.update(
                    tier,
                    red,
                    blue,
                    bd_red or {},
                    bd_blue or {},
                    outcome.red_bonus_rps if is_qual else {},
                    outcome.blue_bonus_rps if is_qual else {},
                    x_rp_red[1:],
                    x_rp_blue[1:],
                    self._rb_z_map(red + blue, h),
                )
        es = self.events.get(ek)
        if es is None:
            es = _EventState()
            self.events[ek] = es
        for t in red + blue:
            if t not in es.idx:
                m, P = self._global_prior(t, ek, h)
                es.add(t, m, P)
        n = es.n
        mu = es.mu[:n]
        cov = es.cov[:n, :n]
        if self.n == 0:
            m0 = self._mean_total()
            self.tot.mean = m0
            self.tot.var = sig * sig
            self.Ls = m0
            if self.comp:
                # Before data: robot points ~ 15% of the score, fouls ~ 5%.
                self.Lu = 0.05 * m0
                self.foul.mean = 0.05 * m0
                self.Ls = m0 - 3 * self.Lu - self.foul.mean
                self.sh.mean = self.Ls
                self.rob.mean = self.Lu
        w_pcg = 1.0 if is_qual else (c.pcg_po_w if self.n > 0 else 0.0)
        if w_pcg > 0.0 and len(red) == 3 and len(blue) == 3:
            reg = c.pcg_reg
            gam_pcg = self._gamma()
            fa_r, fa_b = self._foul_adj(blue), self._foul_adj(red)
            lvl3 = self._level_parts(3)
            z_r = (rsc_clean - lvl3 - fa_r) / sig + gam_pcg * feats[2]
            z_b = (bsc_clean - lvl3 - fa_b) / sig + gam_pcg * feats[0]
            e_ata, e_atb, e_z = self._get_ev_pcg(ek)
            for teams, z_obs in ((red, z_r), (blue, z_b)):
                for t in teams:
                    if t not in self.s_atb:
                        z0 = self._prior_z_scalar(t, h)
                        self.team_z0[t] = z0
                        self.s_atb[t] = reg * z0
                        self.pcg_z[t] = z0
                    self.s_atb[t] += w_pcg * z_obs
                    row_global = self.s_ata.setdefault(t, {})
                    for u in teams:
                        row_global[u] = row_global.get(u, 0.0) + w_pcg
                    evs_t = self.team_events.setdefault(t, [])
                    if not evs_t or evs_t[-1] != ek:
                        if ek not in evs_t:
                            evs_t.append(ek)
                    if t not in e_z:
                        e_z[t] = self._team_latest_pcg_z(t, ek, h)
                    e_atb[t] = e_atb.get(t, 0.0) + w_pcg * z_obs
                    row_ev = e_ata.setdefault(t, {})
                    for u in teams:
                        row_ev[u] = row_ev.get(u, 0.0) + w_pcg
            self._solve_event_pcg(ek, reg)
        sides: List[
            Tuple[List[TeamKey], float, Optional[List[float]], Optional[float]]
        ] = []
        for side_bd, teams, total in (
            (bd_red, red, rsc_clean),
            (bd_blue, blue, bsc_clean),
        ):
            rpts = fpts = None
            if self.comp:
                rpts = robot_points(season, side_bd, len(teams))
                fpts = foul_points(side_bd)
            sides.append((teams, float(total), rpts, fpts))

        rows: List[np.ndarray] = []
        ys: List[float] = []
        kinds: List[str] = []
        gam = self._gamma()
        a_c = self._agg_coef()
        ag_upd: List[Tuple[np.ndarray, float]] = []
        opp_of = {0: 1, 1: 0}
        for j_side, (teams, total, rpts, fpts) in enumerate(sides):
            idx = [es.idx[t] for t in teams]
            oidx = [es.idx[t] for t in sides[opp_of[j_side]][0]]
            # Rank weights at the pre-update means (extended Kalman filter linearization).
            s_o, s_p = mu[idx], mu[oidx]
            t_o, t_p = s_o + mu[[i + 1 for i in idx]], s_p + mu[[i + 1 for i in oidx]]
            w_own = self._agg_w(s_o, t_o, a_c[0], a_c[1])
            w_opp = self._agg_w(s_p, t_p, a_c[2], a_c[3]) - 1.0 - gam
            x_ag = np.concatenate(
                [self._rank_x(s_o, t_o)[0], self._rank_x(s_p, t_p)[0]]
            )
            if self.comp and rpts is not None and fpts is not None:
                hrow = np.zeros(n)
                hrow[idx] = w_own
                hrow[oidx] = w_opp
                shared = total - fpts - sum(rpts)
                rows.append(hrow)
                yv = (shared - self.Ls) / sig
                ys.append(yv)
                kinds.append("s")
                x = -float(mu[oidx].sum())
                e0 = yv - float(mu[idx].sum())
                self.g_xy += x * e0
                self.g_xx += x * x
                ag_upd.append(
                    (x_ag, yv - float(mu[idx].sum()) + gam * float(mu[oidx].sum()))
                )
                for i, pts in zip(idx, rpts):
                    hr = np.zeros(n)
                    hr[i + 1] = 1.0
                    rows.append(hr)
                    ys.append((pts - self.Lu) / sig)
                    kinds.append("u")
            else:
                hrow = np.zeros(n)
                hrow[idx] = 1.0
                hrow[[i + 1 for i in idx]] = 1.0
                hrow[idx] = w_own
                hrow[oidx] = w_opp
                rows.append(hrow)
                yv = (total - self._level_parts(len(teams))) / sig
                ys.append(yv)
                kinds.append("t")
                x = -float(mu[oidx].sum())
                e0 = yv - float(mu[idx].sum() + mu[[i + 1 for i in idx]].sum())
                self.g_xy += x * e0
                self.g_xx += x * x
                e_l = (
                    yv
                    - float(mu[idx].sum() + mu[[i + 1 for i in idx]].sum())
                    + gam * float(mu[oidx].sum())
                )
                ag_upd.append((x_ag, e_l))
        if len(ag_upd) == 2:
            # Fit the rank weights on within-match differences (cancels common offsets).
            dx = ag_upd[0][0] - ag_upd[1][0]
            de = ag_upd[0][1] - ag_upd[1][1]
            self.ag_xx += np.outer(dx, dx)
            self.ag_xe += dx * de
        H = np.array(rows)
        y = np.array(ys)
        m_obs = len(ys)
        R = np.zeros((m_obs, m_obs))
        s_rows = [j for j, k in enumerate(kinds) if k in ("s", "t")]
        for j, k in enumerate(kinds):
            if k == "s":
                R[j, j] = h["rs"]
            elif k == "u":
                R[j, j] = h["ru"]
            else:
                R[j, j] = h["rs"] + 3 * h["ru"] + h["rf"]
        if len(s_rows) == 2:
            a, b = s_rows
            R[a, b] = R[b, a] = c.noise_corr * math.sqrt(R[a, a] * R[b, b])
        PHt = cov @ H.T
        HPH = H @ PHt
        S = HPH + R
        e = y - H @ mu
        # Huber weights on the shared/total rows: an innovation beyond robust_c standard
        # deviations gets the effective variance S_jj * |r| / robust_c.
        rc = c.robust_c
        sc = np.ones(m_obs)
        for j in s_rows:
            r_j = abs(float(e[j])) / math.sqrt(max(S[j, j], 1e-12))
            if r_j > rc:
                tgt = S[j, j] * r_j / rc
                sc[j] = math.sqrt(max((tgt - HPH[j, j]) / max(R[j, j], 1e-12), 1.0))
        if np.any(sc > 1.0):
            R = R * np.outer(sc, sc)
            S = HPH + R
        K = np.linalg.solve(S, PHt.T).T
        mu += K @ e
        cov -= K @ PHt.T
        # Team strength drifts between matches: add process noise to the teams that played.
        S0 = self._prior_cov(h)
        for t in red + blue:
            i = es.idx[t]
            cov[i : i + 2, i : i + 2] += c.q_match * S0
        for t in red + blue:
            i = es.idx[t]
            self.teams[t] = (
                mu[i : i + 2].copy(),
                cov[i : i + 2, i : i + 2].copy(),
                season,
                ek,
            )

        # ---- season statistics (all in points)
        for _teams, total, _rpts, _fpts in sides:
            self.n += 1
            self.tot.add(total, c.level_prior_n, c.level_min_w, c.var_prior_n)
        w = max(1.0 / (self.n + c.level_prior_n), c.level_min_w)
        for j, k in enumerate(kinds):
            ep = e[j] * sig
            mv = HPH[j, j] * sig * sig
            if k == "s":
                self.Ls += w * ep
                self.rs_sum += ep * ep - mv
                self.rs_n += 1
            elif k == "u":
                self.nu += 1
                wu = max(1.0 / (self.nu + c.level_prior_n), c.level_min_w)
                self.Lu += wu * ep
                self.ru_sum += ep * ep - mv
                self.ru_n += 1
            else:
                self.Ls += w * ep
        if self.comp:
            fmean = self.foul.mean
            for j_side, (_teams, _total, _rpts, fpts) in enumerate(sides):
                if fpts is None:
                    continue
                opp = sides[opp_of[j_side]][0]
                dev = (fpts - fmean) / max(len(opp), 1)
                for t in opp:
                    sm, cnt = self.fteam.get(t, (0.0, 0.0))
                    self.fteam[t] = (sm + dev, cnt + 1.0)
        for _teams, total, rpts, fpts in sides:
            if self.comp and rpts is not None and fpts is not None:
                self.foul.add(fpts, c.level_prior_n, c.level_min_w, c.var_prior_n)
                self.sh.add(
                    total - fpts - sum(rpts), c.level_prior_n, 0.0, c.var_prior_n
                )
                for pts in rpts:
                    self.rob.add(pts, c.level_prior_n, 0.0, c.var_prior_n)
        # ---- DQ-rate statistics (written after every forecast input above is fixed)
        for teams, dqs in ((red, outcome.red_dqs), (blue, outcome.blue_dqs)):
            dq_set = set(dqs)
            for t in teams:
                dqn, cnt = self.dq_t.get(t, (0.0, 0.0))
                self.dq_t[t] = (dqn + (1.0 if t in dq_set else 0.0), cnt + 1.0)
