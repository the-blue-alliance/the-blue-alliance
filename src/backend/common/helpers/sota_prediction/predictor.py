"""HKF: hierarchical Kalman filter FRC match predictor.

Each team has a two-dimensional latent strength per season, measured in units of
the season's alliance-score standard deviation (sigma):

* ``s``: contribution to the shared alliance score (game pieces, bonuses).
* ``u``: points the rulebook attributes to this robot alone (auto mobility,
  endgame climb or park). The TBA breakdown records these per driver station.

Observations per alliance: the shared score (total minus robot points minus foul
points received) and one robot-points value per station. Foul points depend on
the opponent, so they enter the forecast as a season mean and a noise term only.

Within an event, the filter keeps a full covariance over all teams at that event.
Between events and seasons, only each team's marginal state is kept.

Win probability:

1. The filter gives a margin mean ``d`` and variance ``v``.
2. An empirical, symmetric CDF of standardized margin residuals maps ``d/sqrt(v)``
   to a probability. The CDF is learned online (normal prior, pooled past seasons,
   current season).
3. An online Bayesian logistic regression (the stacker) combines that logit with a
   slow win-outcome rating (Elo-like, no decay across seasons) and a few antisymmetric
   red - blue features. The weights drift.

Scores: a PMF on the integers >= 0 with an empirical residual shape. The mean is the
filter forecast plus an event-progress offset, an online recalibration and a
foul-transfer term. The point estimate equals the PMF mean.

Ranking points (qualification matches): win and tie RP values times their
probabilities plus bonus RP probabilities from the rulebook model (``bonus.py``),
with the online logistic model (``rp.py``) as the fallback. ``median_rp`` is the
median of a joint RP PMF (``rp_pmf.py``).

Every online learner uses only matches that were played before the forecast.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.special import ndtr

from .base import BasePredictor
from .bonus import RuleBonusModel, tier_of
from .context import MatchContext
from .gmm_shape import BucketGmmShape, GmmShape
from .outcome import MatchOutcome
from .predictions import (
    MatchPrediction,
    PMF,
    RankingPointsPrediction,
    ScorePrediction,
)
from .rp import BonusModel, OnlineLogit
from .rp_pmf import rp_values, RPJoint
from .rulebook import (
    foul_points,
    playoff_bonus_points,
    robot_points,
    SUPPORTED_SEASONS,
)
from .structure import ScoreStructure

logger = logging.getLogger(__name__)

# Released configuration. The boolean switches are ablation switches: every one is on.
# docs/ablation_log.md records the evidence for each value.
DEFAULTS: Dict[str, Any] = {
    # ---- Team state and filter dynamics
    "team_share": 0.6,  # prior share of alliance-score variance explained by teams
    "rho": 0.78,  # season-to-season mean carryover of normalized team strength
    "rho_v": 0.75,  # season-to-season covariance carryover of normalized team strength
    "rookie_z": -0.5,  # rookie prior mean in units of team sd
    "q_event": 0.05,  # process variance added at a new event (fraction of prior cov)
    "drift_event": 0.13,  # mean total z change when a team starts a new event
    "q_match": 0.003,  # process variance (fraction of prior cov) added per match played
    "noise_corr": 0.05,  # correlation of red and blue shared-score noise
    "robust_c": 2.2,  # Huber threshold on standardized shared/total innovations (0: off)
    "components": True,  # use the per-robot and foul decomposition when available
    "robot_team_share": 0.5,  # prior share of robot-points variance explained by teams
    "kappa": 0.5,  # prior correlation between shared and robot team strength
    "hyper_n": 1000.0,  # pseudo count for online noise and spread estimates
    "online_hyper": True,  # learn the noise and spread hyperparameters online
    "interaction": True,  # learn the opponent interaction gamma per season
    "gamma_k0": 200.0,  # shrinkage of gamma toward 0 (units of summed x^2)
    "hist_beta": 0.35,  # weight of older seasons' mean strength in the new-season prior
    "hist_k": 3,  # number of older seasons averaged
    "level_prior_n": 5.0,  # pseudo count of the season score level
    "level_min_w": 1.0 / 3000.0,  # floor of the season level update weight
    "var_prior_n": 30.0,  # pseudo count of the season score variance
    "var_min_w": 0.0,  # floor of the season variance update weight
    # Season scale fix (E1a). False: the season variance averages squared deviations from a
    # mean that is still converging, so a scale change between seasons inflates sigma for
    # ~1,000 alliance scores. True: sigma^2 blends a prior (prev_cv * current level)^2 with the
    # centered (Welford) variance of this season's data, weight var_prior_n. The component
    # spreads in _hyper also use the centered variances.
    "scale_fix": False,
    "scale_fix_w": 0.0,  # forgetting floor of the centered variance (0: cumulative over the season)
    # E1a-pmf: use the scale_fix variance only for the score PMF width (and its calibrators).
    # The filter keeps the default sigma, so team variances and win forecasts do not change.
    "scale_fix_pmf": False,
    # Preseason (TBA event_type 100, "week 0") matches. The benchmark stream has none, so
    # these switches matter only for a stream that includes them.
    # "off": treat them as any other match. "stats" (default, experiment E1b): update only the
    # season statistics (level, variance, component means, noise sums) and no team state or
    # learner. "team": as "stats", plus team state with the observation noise times w0_k.
    "w0_mode": "stats",
    # E1d: week-0 residuals also feed this season's progress-offset bins (needs w0_mode != "off").
    "w0_prog": False,
    "w0_k": 4.0,
    # Rank-weighted alliance aggregation: the alliance score is convex in team strength,
    # so the strongest robot counts more and the weakest robot less than a plain sum.
    "agg": True,  # rank weights on the shared strength s in the filter
    "agg_k": 320.0,  # ridge pseudo count (sum of x^2 units) of the per-season rank weights
    "agg_opp": True,  # also learn rank weights for the opponent's shared strength
    "agg_diff": True,  # fit rank weights on within-match differences (cancels common offsets)
    # Cross-event deconfounding: 3-team alliance normal equations solved by warm-started CG.
    "cross_pcg": True,  # cross-event rating, stacker residual and carryover blend
    "pcg_reg": 8.0,  # ridge regularization (match count units) of the cross-event solver
    "pcg_carry": 0.50,  # blend weight of the cross-event rating into season-end carryover
    "pcg_step": 50,  # match interval between warm-started CG updates
    "pcg_ev_carry": 0.25,  # blend weight of the cross-event rating at a new event (0: off)
    "pcg_po_w": 0.5,  # weight of 3v3 playoff matches in the normal equations (0: off)
    "pcg_prog_debias": True,  # subtract within-event progress offset pre_po in PCG normal equations
    "event_pcg": False,  # two-level staged per-event PCG (False: season-wide periodic CG)
    "dedrift_carry": True,  # subtract the season-end mean team drift before carryover
    # ---- Win probability
    "shape": "emp",  # margin CDF: "normal" or "emp" (empirical standardized residuals)
    "shape_bw": 0.05,  # bin width of the empirical CDF (standardized units)
    "shape_B": 8.0,  # support half-width of the empirical CDF
    "shape_kn": 2000.0,  # pseudo count of the normal prior shape
    "shape_kp": 2000.0,  # pseudo count of the pooled past-season shape
    "stack": True,  # combine the filter logit with the win rating and features below
    "elo_k": 0.03,  # win-rating step per team (logit units)
    "elo_rho": 1.0,  # season-to-season carryover of the win rating
    "stack_pv": 0.1,  # prior variance of the stacking weights (prior mean [1, 0, ...])
    "stack_q": 3e-6,  # per-match random-walk variance of the stacking weights
    "stack_early": 50.0,  # season-progress interaction: decay constant in matches (0: off)
    "stack_agg": True,  # red - blue total strength of the top and the bottom team
    "stack_nev": True,  # red - blue sum of earlier events played this season
    "stack_vt": True,  # red - blue alliance predictive variance
    "stack_lvl": True,  # lf * S, S = mean expected alliance z (heteroscedastic margin)
    "stack_lvl_sat": False,  # concave saturation of S > 0 in stack_lvl (prevents high-S logit collapse)
    "stack_lvl_s0_qm": 3.0,  # saturation scale S_0 for S > 0 in qualification matches
    "stack_lvl_s0_po": 1.5,  # saturation scale S_0 for S > 0 in playoff matches
    "stack_po": False,  # playoff stacker interactions [rank_bot, u_diff, pcg_res] + stack_agg season shrinkage
    "stack_agg_shrink": 0.25,  # season-start shrinkage of collinear stack_agg weights toward 0
    "stack_po_pv": 0.02,  # prior variance of the playoff stacker features
    "stack_dq": True,  # red - blue sum of shrunk team DQ rates (qualification matches only)
    "dq_k": 50.0,  # pseudo count (matches) of the team DQ-rate shrinkage
    "dq_r0": 0.02,  # prior team DQ rate
    # ---- Scores
    "pmf": True,  # emit a score PMF. The point estimate is its mean
    # Empirical score-residual shape: the PMF is mean + sd * T, where T follows the online
    # distribution of standardized alliance-score residuals (not symmetrized), shifted to
    # mean 0 so that the shape changes only the PMF shape.
    "sshape": True,
    "sshape_kn": 2000.0,  # pseudo count of the normal prior
    "sshape_kp": 2000.0,  # pseudo count of the pooled past seasons
    # Smooth shape (E3-gmm, models/hkf/gmm_shape.py): T is a K-component Gaussian mixture fit
    # online by EM to the same weighted residual data, instead of 0.05-sd bins.
    "sshape_gmm": False,
    "sshape_gmm_k": 5,  # mixture components (DEV: K = 3 worse, K = 5 slightly better than 4)
    "sshape_gmm_bw": 0.01,  # fine grid of the residual counts (standardized units)
    "sshape_gmm_refit": 25,  # refit after this many new residuals (and at each season start)
    "sshape_gmm_roll_iters": 2000,  # EM iterations of the season-start refit (converged)
    # Prior weights of the GMM shape. The bins need 2000 each to damp bin noise. The mixture is
    # already smooth, so a small normal prior fits early-season residuals better (DEV grid).
    "sshape_gmm_kn": 500.0,  # pseudo count of the normal prior
    "sshape_gmm_kp": 500.0,  # pseudo count of the pooled past seasons
    # Read-time width knobs of the GMM shape (1.0 = off). widen: wider components, same variance.
    # sdscale: wider components, larger variance. See GmmShape._read_params. sdscale 1.02 fixes the
    # small interval under-coverage of the kn = kp = 500 mixture (DEV gate, e3_gmm.md).
    "sshape_gmm_widen": 1.0,
    "sshape_gmm_sdscale": 1.02,
    # Conditional shape (E3c, docs/experiments/e3c_conditional_shape.md). One GMM per match bucket,
    # shrunk toward the global GMM with weight kg. Buckets: "lvl" = qual / playoff, "x" = score
    # level x (x < lo, lo <= x <= hi, x > hi), "xl" = both. x is the argument of _var_mult.
    "sshape_gmm_cond": "off",
    "sshape_gmm_cond_kg": 2000.0,
    "sshape_gmm_cond_lo": 0.0,
    "sshape_gmm_cond_hi": 0.75,
    # Forecasts use the global GMM for the first N matches of each season (buckets still learn).
    # Early-season score means have an x-dependent bias that a centered bucket shape turns into skew.
    "sshape_gmm_cond_guard": 0,
    # Online per-season ridge recalibration of the score mean: y - m = a + c * (m - level).
    "score_cal": True,
    "score_cal_ka": 500.0,  # ridge pseudo count of the intercept (standardized units)
    "score_cal_kc": 500.0,  # ridge pseudo count of the slope term (sum of x^2 units)
    "score_cal_decay": 0.999,  # per-alliance forgetting factor of the calibration sums
    # Foul transfer: each team has a shrunk rate of foul points it gives to the opponent.
    # The rate moves the opponent's expected foul points (score means only, not the margin).
    "foul_team": True,
    "foul_k": 10.0,  # pseudo count (matches) of the shrinkage of team foul rates to 0
    # Event-progress offset: mean score residual (sigma units) per bin of the number of
    # matches the alliance's teams already played at the event, learned per season.
    # Scores rise within an event. The offset moves the score means, not the margin.
    "prog_off": True,
    "prog_pool": True,  # pool zero-centered within-event progress offsets across past seasons
    "prog_bins": 12,
    "prog_k": 20.0,  # pseudo count (alliance scores) of the shrinkage per bin
    "prog_rp": True,  # add the offset to the bonus-RP features
    "prog_filter_debias": False,  # ablation: subtract prog_off from the Kalman filter innovation yv
    # Online Huber-clipped ridge score calibration for playoff progression/defense (po_score_cal)
    # and multi-elite rank sub-additivity / cannibalization (rank_score_cal).
    "po_score_cal": False,
    "rank_score_cal": False,
    "sat_k": 300.0,  # ridge pseudo count of the online score saturation learner
    "sat_huber": 0.65,  # Huber threshold (sigma units) on standardized score residuals
    "sat_pool_decay": 0.85,  # season-to-season pooling decay of the normal equations
    # Rulebook lattice: an online per-season categorical of y mod lat_p (Dirichlet prior
    # lat_a per residue) reweights the score PMF (2017: 5-point steps). The period must be
    # much smaller than the PMF sd, otherwise y mod lat_p learns the score level itself.
    "lattice": True,
    "lat_p": 10,  # period; 10 covers the increments 2 and 5
    "lat_a": 10.0,  # Dirichlet pseudo count per residue
    # Rules-free score structure (E2c + E2-sel, models/hkf/structure.py). Online discovery of
    # score components from score_breakdown fields, a component PMF, and a causal mixture of
    # the base PMF and the base PMF times the component fine structure. Use with lattice off.
    "score_struct": False,
    "struct_eta": 0.5,  # learning rate of the mixture weights (per alliance log p(y))
    "struct_alpha": 1e-3,  # fixed-share rate of the mixture weights per match
    "struct_lam": 0.25,  # shrinkage of the mixture weights toward uniform at a season start
    # Online per-season variance recalibration of the score PMF: E[z^2] = c0 + c1 * x, with z
    # the standardized alliance-score residual and x = (mean - level) / sigma. A score is a sum
    # of scoring actions, so its error scale grows with the expected score. Ridge prior:
    # c0 = 1, c1 = 0. The PMF sd is multiplied by sqrt(c0 + c1 x).
    "var_cal": True,
    "var_cal_k": 250.0,  # ridge pseudo count of both coefficients
    "var_cal_decay": 0.999,  # per-alliance forgetting factor of the sums
    "var_cal_floor": 0.25,  # lower bound of the variance multiplier
    # 2016/2017 playoff threshold bonuses (score points in playoffs, RPs in qualification).
    "playoff_bonus": True,
    # Within-event fixed 3-team playoff alliance residual persistence.
    "playoff_synergy": True,
    "po_syn_k": 2.0,  # pseudo count (playoff matches) of the alliance residual shrinkage
    "po_syn_s": 0.25,  # playoff alliance residual weight on expected score (sigma units)
    "po_syn_d": 0.25,  # playoff alliance residual weight on standardized win margin
    # ---- Ranking points
    "rp": True,  # emit ranking point forecasts for qualification matches
    "rp_prior_var": 4.0,  # prior variance of each bonus RP logistic weight
    "rp_q": 1e-4,  # per-match random-walk variance of the bonus RP intercept
    "rp_agg": True,  # add own-alliance rank features to the rulebook bonus calibration
    # Rulebook bonus RP model (models/hkf/bonus.py). The logistic model above stays
    # as the fallback for keys without channel data (first matches of a season).
    "rp_rule": True,  # use rulebook thresholds on team channels for bonus RPs
    "rb_q_frac": 0.02,  # per-match process variance of team sum channels (fraction of prior)
    "rb_prior_share": 0.5,  # prior share of alliance channel variance explained by teams
    "rb_z_prior": 0.70,  # pre-season standardized team skill weight in the SumChannel cold start
    "rb_decay": 0.95,  # per-observation decay of team counts in robot and binary channels
    "rb_prior_n": 3.0,  # pseudo count of the season mix in team robot and binary channels
    "rb_cal_pv": 0.5,  # prior variance of the rule calibration weights (prior mean [0, 1])
    "rb_cal_q": 1e-5,  # per-match random-walk variance of the calibration weights
    "rb_flag": True,  # add a team propensity on the bonus flag itself to the calibration model
    "rb_mix": True,  # add the score-filter features to the rule calibration model
    "rb_tier": True,  # use event-type thresholds (False: regional thresholds everywhere)
    "rb_rule_feat": True,  # feed logit(p_rule) to the calibration model
    "rb_award": True,  # learn the rate of flags awarded without the rule (fouls, exemptions)
    "rb_award_a": 0.5,  # Beta prior of the award and deny rates
    "rb_award_b": 20.0,
    # RP median (models/hkf/rp_pmf.py): a joint RP PMF from P(win), P(tie) and the bonus
    # probabilities, with a Gaussian copula on the match outcome. median_rp is its median.
    # expected_rp stays the mean. rho_k (bonus vs. outcome) is learned per season and key.
    "rp_median": True,
    "rp_rho_prior": 0.3,  # prior mean of rho_k
    "rp_rho_sd": 0.2,  # prior sd of rho_k
}


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _solve_pcg_dict(
    ata: Dict[str, Dict[str, float]],
    atb: Dict[str, float],
    reg: float,
    x0: Dict[str, float],
    iters: int = 5,
) -> Dict[str, float]:
    """Warm-started conjugate gradient solver for (A^T A + reg * I) x = A^T b."""
    teams = list(atb.keys())
    if not teams:
        return {}
    x = {t: x0.get(t, 0.0) for t in teams}
    r = {}
    for t in teams:
        ax = reg * x[t] + sum(w * x[u] for u, w in ata.get(t, {}).items())
        r[t] = atb[t] - ax
    d = dict(r)
    rs_old = sum(v * v for v in r.values())
    if rs_old < 1e-12:
        return x
    for _ in range(iters):
        ad = {}
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


class _Run:
    """Running mean and variance with a pseudo-count prior and optional floor weight.

    It also keeps centered moments of the data alone (``wm``, ``wm2``), with no prior. The
    weight of point n is max(1/n, cen_w). With cen_w = 0 this is the Welford population
    variance. With cen_w > 0 old points are forgotten, so a drift of the season mean does not
    accumulate in ``data_var``.
    """

    __slots__ = ("mean", "n", "var", "wm", "wm2", "cen_w")

    def __init__(self, mean: float = 0.0, var: float = 1.0, cen_w: float = 0.0) -> None:
        self.n = 0
        self.mean = mean
        self.var = var
        self.wm = 0.0
        self.wm2 = 0.0
        self.cen_w = cen_w

    def add(
        self, x: float, prior_n: float, min_w: float, prior_nv: float, min_wv: float
    ) -> None:
        self.n += 1
        w = max(1.0 / (self.n + prior_n), min_w)
        d = x - self.mean
        self.mean += w * d
        wv = max(1.0 / (self.n + prior_nv), min_wv)
        self.var += wv * (d * d - self.var)
        # Exponentially weighted centered variance (West 1979): exact Welford while 1/n > cen_w.
        wc = max(1.0 / self.n, self.cen_w)
        dw = x - self.wm
        self.wm += wc * dw
        self.wm2 = (1.0 - wc) * (self.wm2 + wc * dw * dw)

    @property
    def data_var(self) -> float:
        """Centered variance of the observed data (0 before 2 points)."""
        return self.wm2 if self.n > 1 else 0.0


class _EventState:
    """Joint Gaussian state of every team at one event: mean and full covariance over [s, u] pairs."""

    __slots__ = ("cov", "idx", "mu", "n")

    def __init__(self, cap: int = 128) -> None:
        self.idx: Dict[str, int] = {}  # team -> base index (s at i, u at i + 1)
        self.mu = np.zeros(cap)
        self.cov = np.zeros((cap, cap))
        self.n = 0

    def add(self, team: str, m: np.ndarray, P: np.ndarray) -> int:
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


class HKFPredictor(BasePredictor):
    """Standalone hkf predictor (see the module docstring). Keyword params override ``DEFAULTS``."""

    is_standalone: bool = True
    external_dependencies: Tuple[str, ...] = ()

    def __init__(self, name: str = "hkf", **params: Any) -> None:
        super().__init__(name=name)
        unknown = set(params) - set(DEFAULTS)
        if unknown:
            raise ValueError(f"unknown params {sorted(unknown)}")
        self.p = {**DEFAULTS, **params}
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self) -> None:
        """Clear all learned state."""
        # team -> (m[2], P[2x2], season, event_key)
        self.teams: Dict[str, Tuple[np.ndarray, np.ndarray, int, str]] = {}
        self.events: Dict[str, _EventState] = {}
        self.processed_match_keys: set[str] = set()
        self.season: Optional[int] = None
        self.prev_mean: Optional[float] = None
        self.prev_cv: float = 0.5
        self.hist: Dict[str, List[Tuple[int, float]]] = {}
        self._shape_init()
        self.wr: Dict[str, Tuple[float, int]] = {}  # win rating: team -> (r, season)
        pv = self.p["stack_pv"]
        dim = 4 if self.p["stack_early"] > 0 else 2
        dim += 2 if self.p["stack_agg"] else 0
        dim += 1 if self.p["stack_nev"] else 0
        dim += 1 if self.p["stack_vt"] else 0
        dim += 1 if self.p["cross_pcg"] else 0
        dim += 1 if self.p["stack_lvl"] else 0
        dim += 1 if self.p["stack_dq"] else 0
        if self.p["stack_po"]:
            dim += 3
        pvs = [pv] * dim
        if self.p["stack_po"]:
            po_pv = float(self.p["stack_po_pv"])
            pvs[-3:] = [po_pv, po_pv, po_pv]
        self.stacker = OnlineLogit(
            dim,
            pvs,
            self.p["stack_q"],
            prior_mean=[1.0] + [0.0] * (dim - 1),
            q_all=True,
        )
        self.ag_hist: List[np.ndarray] = []  # final rank weights of past seasons
        self.ag_prior = np.zeros(4)
        self.sat_dim = 6
        self.sat_xx_pool = np.zeros((self.sat_dim, self.sat_dim))
        self.sat_xe_pool = np.zeros(self.sat_dim)
        self.sat_w = np.zeros(self.sat_dim)
        self.qm_s_mean = np.array([0.55, -0.03, -0.58, 0.09])
        self.qm_s_n = 100.0
        self.scount: Dict[str, int] = {}  # matches played this season, per team
        self.nevc: Dict[str, Tuple[int, str]] = (
            {}
        )  # team -> (earlier events this season, current event)
        self.bonus = BonusModel([self.p["rp_prior_var"]] * 4, self.p["rp_q"])
        self.rbonus = RuleBonusModel(self.p)
        self.rpj = RPJoint(
            rho_prior=self.p["rp_rho_prior"], rho_prior_sd=self.p["rp_rho_sd"]
        )
        self.tier_fallbacks = (
            0  # qm updates whose tier came from the event key (no event_type)
        )
        self.tier_fallback_events: set = set()
        nb = len(self.sh_norm)
        self.ss_pool = np.zeros(nb)
        self.ss_pool_n = 0.0
        self.ss_cur = np.zeros(nb)
        self.ss_cur_n = 0.0
        self._ss_refresh()
        self.gmm: Optional[GmmShape] = (
            GmmShape(
                self.p["shape_B"],
                self.p["sshape_gmm_bw"],
                int(self.p["sshape_gmm_k"]),
                self.p["sshape_gmm_kn"],
                self.p["sshape_gmm_kp"],
                int(self.p["sshape_gmm_refit"]),
                int(self.p["sshape_gmm_roll_iters"]),
                float(self.p["sshape_gmm_widen"]),
                float(self.p["sshape_gmm_sdscale"]),
            )
            if self.p["sshape_gmm"]
            else None
        )
        # E3c buckets, all created here so that predict_match never changes state.
        self.gmm_b: Dict[Any, BucketGmmShape] = {}
        mode = self.p["sshape_gmm_cond"]
        if self.gmm is not None and mode != "off":
            xs = (0, 1, 2) if mode in ("x", "xl") else (None,)
            ls = (True, False) if mode in ("lvl", "xl") else (None,)
            for xk in xs:
                for lk in ls:
                    self.gmm_b[(xk, lk)] = BucketGmmShape(
                        self.gmm,
                        self.p["sshape_gmm_cond_kg"],
                        self.p["shape_B"],
                        self.p["sshape_gmm_bw"],
                        int(self.p["sshape_gmm_k"]),
                        self.p["sshape_gmm_kp"],
                        int(self.p["sshape_gmm_refit"]),
                        int(self.p["sshape_gmm_roll_iters"]),
                        float(self.p["sshape_gmm_widen"]),
                        float(self.p["sshape_gmm_sdscale"]),
                    )
        self.pg_pool = np.zeros(
            (2, int(self.p["prog_bins"]))
        )  # past seasons: centered sum r/sig, n
        self.struct: Optional[ScoreStructure] = (
            ScoreStructure(
                self.p["struct_eta"], self.p["struct_alpha"], self.p["struct_lam"]
            )
            if self.p["score_struct"]
            else None
        )
        self._new_season_stats()

    def _new_season_stats(self) -> None:
        self.n = 0
        cw = float(self.p["scale_fix_w"])
        self.tot = _Run(cen_w=cw)  # raw alliance totals
        self.Ls = 0.0  # shared level (points per alliance), residual driven
        self.Lu = 0.0  # robot level (points per robot), residual driven
        self.nu = 0
        self.foul = _Run(cen_w=cw)  # foul points received per alliance
        self.sh = _Run(cen_w=cw)  # raw shared points per alliance (spread)
        self.rob = _Run(cen_w=cw)  # raw robot points (spread)
        self.rs_sum = 0.0  # sum of (e_s^2 - model var), points^2
        self.rs_n = 0
        self.ru_sum = 0.0
        self.ru_n = 0
        self.g_xy = 0.0
        self.g_xx = 0.0
        self.sc = np.zeros(
            5
        )  # score calibration sums: n, sum x, sum x^2, sum e, sum x e
        self.vc = np.zeros(
            5
        )  # variance calibration sums: n, sum x, sum x^2, sum z^2, sum x z^2
        self.fteam: Dict[str, Tuple[float, float]] = (
            {}
        )  # team -> (sum of foul deviations given, n)
        self.pg_cur = np.zeros(
            (2, int(self.p["prog_bins"]))
        )  # this season: sum r/sig, n
        self.lat_cnt = np.zeros(
            int(self.p["lat_p"])
        )  # this season: counts of y mod lat_p
        self.lat_w = np.ones(int(self.p["lat_p"]))  # residue weights (mean 1)
        self.ecount: Dict[Tuple[str, str], int] = {}  # (event, team) -> matches played
        self.comp = bool(self.p["components"]) and (self.season in SUPPORTED_SEASONS)
        self.ag_xx = np.zeros((4, 4))  # rank-weight regression sums (this season)
        self.ag_xe = np.zeros(4)
        self.sat_xx_cur = np.zeros((self.sat_dim, self.sat_dim))
        self.sat_xe_cur = np.zeros(self.sat_dim)
        self._refresh_sat_w()
        self.s_ata: Dict[str, Dict[str, float]] = {}  # cross-event PCG normal equations
        self.s_atb: Dict[str, float] = {}
        self.pcg_z: Dict[str, float] = {}
        self.pcg_cnt = 0  # matches added to the normal equations
        self.team_events: Dict[str, List[str]] = {}
        self.team_z0: Dict[str, float] = {}
        self.ev_pcg: Dict[
            str, Tuple[Dict[str, Dict[str, float]], Dict[str, float], Dict[str, float]]
        ] = {}
        self.po_res: Dict[Tuple[str, Tuple[str, ...]], List[float]] = (
            {}
        )  # playoff alliance residuals
        self.dq_t: Dict[str, Tuple[float, float]] = {}  # team -> (DQs, matches)

    def start_season(self, season: int) -> None:
        """Pool the finished season into the cross-season priors and reset the season state."""
        if self.n > 0:
            self.prev_mean = self.tot.mean
            v_end = self.tot.data_var if self.p["scale_fix"] else self.tot.var
            self.prev_cv = math.sqrt(max(v_end, 1e-9)) / max(self.tot.mean, 1e-6)
            if self.p["agg"]:
                # Pooled prior of the rank weights: the mean of the past seasons' final values.
                self.ag_hist.append(self._agg_coef())
                self.ag_prior = np.mean(self.ag_hist, axis=0)
            if self.p["prog_pool"] and self.comp:
                cnt = self.pg_cur[1]
                tot_n = float(cnt.sum())
                if tot_n > 0.0:
                    mean_g = float(self.pg_cur[0].sum()) / tot_n
                    self.pg_pool[0] += self.pg_cur[0] - cnt * mean_g
                    self.pg_pool[1] += cnt
            if self.p["po_score_cal"] or self.p["rank_score_cal"]:
                decay_pool = float(self.p["sat_pool_decay"])
                self.sat_xx_pool = decay_pool * self.sat_xx_pool + self.sat_xx_cur
                self.sat_xe_pool = decay_pool * self.sat_xe_pool + self.sat_xe_cur
        if self.season is not None:
            if self.p["cross_pcg"] and self.s_atb:
                reg = float(self.p["pcg_reg"])
                self.pcg_z = _solve_pcg_dict(
                    self.s_ata, self.s_atb, reg, self.pcg_z, iters=10
                )
                w_c = float(self.p["pcg_carry"])
                if w_c > 0.0:
                    for t, st in list(self.teams.items()):
                        if st[2] == self.season and t in self.pcg_z:
                            m, P, s, ev = st
                            cur_t = float(m.sum())
                            new_t = (1.0 - w_c) * cur_t + w_c * self.pcg_z[t]
                            self.teams[t] = (m + 0.5 * (new_t - cur_t), P, s, ev)
            if self.p["dedrift_carry"]:
                vals = [
                    float(st[0].sum())
                    for st in self.teams.values()
                    if st[2] == self.season
                ]
                mean_t = float(np.mean(vals)) if vals else 0.0
                for t, st in list(self.teams.items()):
                    if st[2] == self.season:
                        m, P, s, ev = st
                        self.teams[t] = (m - 0.5 * mean_t, P, s, ev)
            for t, st in self.teams.items():
                if st[2] == self.season:
                    self.hist.setdefault(t, []).append(
                        (self.season, float(st[0].sum()))
                    )
            if (
                self.p["stack_po"]
                and self.p["stack_agg"]
                and float(self.p["stack_agg_shrink"]) > 0.0
            ):
                shrink = float(self.p["stack_agg_shrink"])
                i_agg = 4 if self.p["stack_early"] > 0 else 2
                self.stacker.w[i_agg : i_agg + 2] *= 1.0 - shrink
                pv = float(self.p["stack_pv"])
                for j in (i_agg, i_agg + 1):
                    self.stacker.S[j, j] = min(self.stacker.S[j, j], pv)
        self.season = season
        self.bonus.reset()
        self.rbonus.reset_season(season)
        self.rpj.start_season()
        if self.struct is not None:
            self.struct.start_season()
        if self.ss_cur_n > 0:
            self.ss_pool += self.ss_cur
            self.ss_pool_n += self.ss_cur_n
        self.ss_cur = np.zeros(len(self.ss_cur))
        self.ss_cur_n = 0.0
        self._ss_refresh()
        if self.gmm is not None:
            self.gmm.roll()
            for b in self.gmm_b.values():
                b.roll()
        self._shape_roll()
        self._new_season_stats()
        self.events = {}
        self.scount = {}
        self.nevc = {}
        self.processed_match_keys = set()

    def end_season(self, season: int) -> None:
        """Do nothing. start_season does the season rollover."""

    def prune_dead_state(
        self, active_event_keys: Optional[Sequence[str]] = None
    ) -> None:
        """Prune ephemeral state from concluded events to prevent memory/storage bloat.

        - Discards _EventState covariance matrices for completed events (only marginal team
          ratings in self.teams are carried forward across events).
        - Truncates ScoreStructure raw historical breakdown dicts (disc.hist) to the last 300 rows.
        """
        if active_event_keys is not None:
            active_set = set(active_event_keys)
            concluded = [ek for ek in list(self.events.keys()) if ek not in active_set]
            for ek in concluded:
                del self.events[ek]

        if hasattr(self, "struct") and self.struct is not None:
            if hasattr(self.struct, "disc") and hasattr(self.struct.disc, "hist"):
                if len(self.struct.disc.hist) > 300:
                    self.struct.disc.hist = self.struct.disc.hist[-300:]

    def dump_state(self) -> bytes:
        """Serialize predictor state to compressed binary bytes."""
        import pickle
        import zlib

        return zlib.compress(
            pickle.dumps(self.__dict__, protocol=pickle.HIGHEST_PROTOCOL)
        )

    def load_state(self, data: bytes) -> None:
        """Restore predictor state from compressed binary bytes."""
        import pickle
        import zlib

        state_dict = pickle.loads(zlib.decompress(data))
        self.__dict__.update(state_dict)

    # ------------------------------------------------------- hyperparameters
    def _prog_bin(self, event_key: str, teams: Sequence[str]) -> int:
        n = sum(self.ecount.get((event_key, t), 0) for t in teams) / max(len(teams), 1)
        return min(int(n), int(self.p["prog_bins"]) - 1)

    def _prog_off(self, event_key: str, teams: Sequence[str]) -> float:
        """Expected score residual (points) at this stage of the event."""
        if not self.p["prog_off"] or (self.n == 0 and not self.p["prog_pool"]):
            return 0.0
        b = self._prog_bin(event_key, teams)
        k = float(self.p["prog_k"])
        g0 = 0.0
        if self.p["prog_pool"] and self.pg_pool[1, b] > 0.0:
            g0 = float(self.pg_pool[0, b]) / (float(self.pg_pool[1, b]) + k)
        g = (float(self.pg_cur[0, b]) + k * g0) / (float(self.pg_cur[1, b]) + k)
        return self._sigma() * g

    def _gamma(self) -> float:
        if not self.p["interaction"]:
            return 0.0
        return self.g_xy / (self.g_xx + self.p["gamma_k0"])

    def _sigma(self) -> float:
        if self.n == 0:
            m = self.prev_mean if self.prev_mean is not None else 20.0
            return max(1e-6, self.prev_cv * m)
        if self.p["scale_fix"]:
            k = float(self.p["var_prior_n"])
            nd = float(self.tot.n)
            cw = float(self.p["scale_fix_w"])
            if cw > 0.0:
                nd = min(nd, 1.0 / cw)
            prior_var = (self.prev_cv * max(self.tot.mean, 1e-6)) ** 2
            return math.sqrt(
                max((k * prior_var + nd * self.tot.data_var) / (k + nd), 1e-9)
            )
        return math.sqrt(max(self.tot.var, 1e-9))

    def _pmf_scale(self) -> float:
        """Score PMF sd factor for scale_fix_pmf: the scale_fix sigma over the filter sigma."""
        if not self.p["scale_fix_pmf"] or self.p["scale_fix"] or self.n == 0:
            return 1.0
        k = float(self.p["var_prior_n"])
        nd = float(self.tot.n)
        cw = float(self.p["scale_fix_w"])
        if cw > 0.0:
            nd = min(nd, 1.0 / cw)
        prior_var = (self.prev_cv * max(self.tot.mean, 1e-6)) ** 2
        fix = math.sqrt(max((k * prior_var + nd * self.tot.data_var) / (k + nd), 1e-9))
        return fix / max(self._sigma(), 1e-9)

    def _mean_total(self) -> float:
        if self.n == 0:
            return self.prev_mean if self.prev_mean is not None else 20.0
        return self.tot.mean

    def _hyper(self) -> Dict[str, float]:
        """Season hyperparameters in sigma units: team spreads and noise variances."""
        f = self.p["team_share"]
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
        k = self.p["hyper_n"]
        # Prior split before data: robot points ~ 20% of alliance variance.
        prior_rob_var = 0.2 / 3.0  # per robot, sigma units
        prior_sh_var = 0.7
        prior_foul_var = 0.1
        g = self.p["robot_team_share"]
        if self.p["online_hyper"] and self.n > 0:
            cen = bool(self.p["scale_fix"])
            v_rob = self.rob.data_var if cen else self.rob.var
            v_sh = self.sh.data_var if cen else self.sh.var
            v_foul = self.foul.data_var if cen else self.foul.var
            nr = self.rob.n
            vu = (k * prior_rob_var + nr * v_rob / sig2) / (k + nr)
            ns = self.sh.n
            vs = (k * prior_sh_var + ns * v_sh / sig2) / (k + ns)
            nf = self.foul.n
            vf = (k * prior_foul_var + nf * v_foul / sig2) / (k + nf)
            ru = (k * (1 - g) * prior_rob_var + self.ru_sum / sig2) / (k + self.ru_n)
            rs = (k * (1 - f) * prior_sh_var + self.rs_sum / sig2) / (k + self.rs_n)
        else:
            vu, vs, vf = prior_rob_var, prior_sh_var, prior_foul_var
            ru, rs = (1 - g) * prior_rob_var, (1 - f) * prior_sh_var
        ru = min(max(ru, 0.1 * vu), 0.95 * vu)
        rs = min(max(rs, 0.1 * vs), 0.95 * vs)
        tu2 = max(vu - ru, 1e-4)
        ts2 = max((vs - rs) / 3.0, 1e-4)
        return {
            "ts2": ts2,
            "tu2": tu2,
            "rs": rs,
            "ru": ru,
            "rf": vf,
            "kap": self.p["kappa"],
        }

    @staticmethod
    def _prior_cov(h: Dict[str, float]) -> np.ndarray:
        ts, tu = math.sqrt(h["ts2"]), math.sqrt(h["tu2"])
        c = h["kap"] * ts * tu
        return np.array([[h["ts2"], c], [c, h["tu2"]]])

    # ----------------------------------------------------------- team priors
    def _carry_total(self, team: str, m: np.ndarray, s: int) -> Tuple[float, int]:
        """New-season prior mean of the total strength (s + u) of a team last seen in season s.

        The last-season total is blended with the mean of up to ``hist_k`` older seasons and
        multiplied by rho per season of gap. Returns (mean total, gap).
        """
        gap = max(1, int(self.season - s)) if self.season is not None else 1
        T = float(m.sum())
        beta = self.p["hist_beta"]
        if beta > 0:
            older = [x for (ss, x) in self.hist.get(team, []) if ss < s][
                -self.p["hist_k"] :
            ]
            if older:
                T = (1.0 - beta) * T + beta * (sum(older) / len(older))
        return self.p["rho"] ** gap * T, gap

    def _get_ev_pcg(
        self, event_key: str
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float], Dict[str, float]]:
        st = self.ev_pcg.get(event_key)
        if st is None:
            st = ({}, {}, {})
            self.ev_pcg[event_key] = st
        return st

    def _team_latest_pcg_z(
        self, team: str, event_key: str, h: Dict[str, float]
    ) -> float:
        """Return the most recent per-event PCG rating for ``team``."""
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

    def _solve_event_pcg(self, ek: str, reg: float) -> None:
        """Solve the clamped subgraph normal equations for active teams in ``ek``."""
        e_ata, e_atb, e_z = self._get_ev_pcg(ek)
        active = set(e_atb.keys())
        sub_ata: Dict[str, Dict[str, float]] = {}
        sub_atb: Dict[str, float] = {}
        for t in active:
            b_t = reg * self.team_z0[t]
            row_t: Dict[str, float] = {}
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
        self, team: str, event_key: str, h: Dict[str, float]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prior mean and covariance of a team that enters an event state."""
        S0 = self._prior_cov(h)
        g = S0 @ np.ones(2)
        tT2 = float(g.sum())
        st = self.teams.get(team)
        if st is None:
            m = self.p["rookie_z"] * math.sqrt(tT2) * g / tT2
            return m, S0.copy()
        m, P, s, ev = st
        if s != self.season:
            carried, gap = self._carry_total(team, m, s)
            rv = float(self.p["rho_v"]) ** gap
            vT = float(P.sum())
            mean = carried * g / tT2
            explained = rv * rv * max(tT2 - vT, 0.0)
            explained = min(explained, 0.98 * tT2)
            Pn = S0 - np.outer(g, g) * explained / (tT2 * tT2)
            return mean, Pn
        if ev != event_key:
            q = self.p["q_event"]
            w = g / tT2
            m_new = m + self.p["drift_event"] * w
            w_ev = float(self.p["pcg_ev_carry"]) if self.p["cross_pcg"] else 0.0
            if w_ev > 0.0:
                if self.p["event_pcg"]:
                    pst = self.ev_pcg.get(ev)
                    if pst is not None and team in pst[2]:
                        diff = pst[2][team] - float(m.sum())
                        m_new = m_new + w_ev * diff * w
                elif team in self.pcg_z:
                    diff = self.pcg_z[team] - float(m.sum())
                    m_new = m_new + w_ev * diff * w
            return m_new, P + q * S0
        return m, P

    def _view(
        self, event_key: str, teams: Sequence[str], h: Dict[str, float]
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
        if inside_a:
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
        B, w = self.p["shape_B"], self.p["shape_bw"]
        nb = int(round(2 * B / w))
        edges = np.linspace(-B, B, nb + 1)
        cdf = np.array([_phi(x) for x in edges])
        cdf[0], cdf[-1] = 0.0, 1.0
        self.sh_norm = np.diff(cdf)  # normal prior mass per bin
        self.sh_pool = np.zeros(nb)  # past seasons (normalized counts)
        self.sh_pool_n = 0.0
        self.sh_cur = np.zeros(nb)  # current season counts
        self.sh_cur_n = 0.0
        self._shape_refresh()

    def _shape_add(self, t: float) -> None:
        B, w = self.p["shape_B"], self.p["shape_bw"]
        nb = len(self.sh_cur)
        i = int((min(max(t, -B + 1e-9), B - 1e-9) + B) / w)
        i = min(max(i, 0), nb - 1)
        self.sh_cur[i] += 0.5
        self.sh_cur[nb - 1 - i] += 0.5
        self.sh_cur_n += 1.0
        self._shape_refresh()

    def _shape_roll(self) -> None:
        """Merge the finished season into the pooled shape at a season boundary."""
        if self.sh_cur_n > 0:
            self.sh_pool += self.sh_cur
            self.sh_pool_n += self.sh_cur_n
        self.sh_cur = np.zeros(len(self.sh_cur))
        self.sh_cur_n = 0.0
        self._shape_refresh()

    def _shape_refresh(self) -> None:
        kn, kp = self.p["shape_kn"], self.p["shape_kp"]
        mass = kn * self.sh_norm + self.sh_cur
        if self.sh_pool_n > 0:
            mass = mass + kp * self.sh_pool / self.sh_pool_n
        mass = mass / mass.sum()
        self.sh_mass = mass
        self.sh_cum = np.concatenate(([0.0], np.cumsum(mass)))

    def _win_prob(self, x: float) -> float:
        if self.p["shape"] != "emp":
            return _phi(x)
        if x > 0:
            return 1.0 - self._win_prob(-x)
        B, w = self.p["shape_B"], self.p["shape_bw"]
        if x <= -B:
            return 0.0
        pos = (x + B) / w
        i = min(int(pos), len(self.sh_mass) - 1)
        return float(self.sh_cum[i] + (pos - i) * self.sh_mass[i])

    def _wr_get(self, team: str) -> float:
        st = self.wr.get(team)
        if st is None:
            return 0.0
        r, s = st
        if self.season is not None and s != self.season:
            r *= self.p["elo_rho"] ** max(1, int(self.season - s))
        return r

    def _wr_diff(self, red: Sequence[str], blue: Sequence[str]) -> float:
        return sum(self._wr_get(t) for t in red) - sum(self._wr_get(t) for t in blue)

    @staticmethod
    def _stack_rank(feats: Tuple[float, ...]) -> Tuple[float, ...]:
        """Rank features that the stacker uses: red minus blue [top, bottom] total strength."""
        return feats[6:8]

    def _prior_z_scalar(self, team: str, h: Dict[str, float]) -> float:
        """Scalar total strength (s + u) of a team from the causal state.

        It is the current in-season filter total if the team already played this season,
        else the carried-over new-season prior mean (rookie prior for an unseen team).
        """
        S0 = self._prior_cov(h)
        tT2 = float((S0 @ np.ones(2)).sum())
        st = self.teams.get(team)
        if st is None:
            return self.p["rookie_z"] * math.sqrt(max(tT2, 1e-6))
        m, _, s, _ = st
        if s == self.season:
            return float(m.sum())
        return self._carry_total(team, m, s)[0]

    def _pcg_diff_res(
        self,
        red: Sequence[str],
        blue: Sequence[str],
        feats: Tuple[float, ...],
        h: Dict[str, float],
        event_key: str = "",
    ) -> float:
        """Cross-event PCG rating difference minus local filter total-strength difference."""
        if self.p["event_pcg"]:
            if not self.team_events:
                return 0.0
            pr = sum(self._team_latest_pcg_z(t, event_key, h) for t in red)
            pb = sum(self._team_latest_pcg_z(t, event_key, h) for t in blue)
            tz_diff = (feats[0] + feats[1]) - (feats[2] + feats[3])
            return (pr - pb) - tz_diff
        if not self.pcg_z:
            return 0.0
        pr = sum(
            self.pcg_z[t] if t in self.pcg_z else self._prior_z_scalar(t, h)
            for t in red
        )
        pb = sum(
            self.pcg_z[t] if t in self.pcg_z else self._prior_z_scalar(t, h)
            for t in blue
        )
        tz_diff = (feats[0] + feats[1]) - (feats[2] + feats[3])
        return (pr - pb) - tz_diff

    def _final_prob(
        self,
        p_h: float,
        red: Sequence[str],
        blue: Sequence[str],
        rank: Optional[Sequence[float]] = None,
        event_key: str = "",
        feats: Optional[Tuple[float, ...]] = None,
        h: Optional[Dict[str, float]] = None,
        zs: Optional[Tuple[float, float]] = None,
        comp_level: Optional[str] = "qm",
    ) -> Tuple[float, np.ndarray]:
        """Stacked win probability and the stacker feature vector.

        Every feature is antisymmetric under a red/blue swap, so the stacker (no intercept)
        keeps p(red) = 1 - p(blue). Feature order: [lf, wd, lf e, wd e], rank (2), events
        played, predictive variance, cross-event residual, lf S, DQ rates.
        """
        pc = min(max(p_h, 1e-6), 1.0 - 1e-6)
        lf, wd = math.log(pc / (1.0 - pc)), self._wr_diff(red, blue)
        tau = self.p["stack_early"]
        if tau > 0:
            teams = list(red) + list(blue)
            n = sum(self.scount.get(t, 0) for t in teams) / max(len(teams), 1)
            e = math.exp(-n / tau)
            x = np.array([lf, wd, lf * e, wd * e])
        else:
            x = np.array([lf, wd])
        if self.p["stack_agg"]:
            x = np.concatenate(
                [x, np.asarray(rank if rank is not None else (0.0, 0.0), dtype=float)]
            )
        if self.p["stack_nev"]:
            x = np.append(x, self._nev(red, event_key) - self._nev(blue, event_key))
        if self.p["stack_vt"]:
            x = np.append(x, float(feats[4] - feats[5]) if feats is not None else 0.0)
        pcg_r = 0.0
        if self.p["cross_pcg"]:
            pcg_r = (
                self._pcg_diff_res(red, blue, feats, h or self._hyper(), event_key)
                if feats is not None
                else 0.0
            )
            x = np.append(x, pcg_r)
        if self.p["stack_lvl"]:
            # Count noise grows with the expected score, so the same strength gap is less decisive
            # in a high-scoring match. S is the mean expected alliance z above the season level.
            S = 0.5 * (zs[0] + zs[1]) if zs is not None else 0.0
            if self.p["stack_lvl_sat"] and S > 0.0:
                is_qm_lvl = (comp_level or "qm") == "qm"
                s0 = float(
                    self.p["stack_lvl_s0_qm"]
                    if is_qm_lvl
                    else self.p["stack_lvl_s0_po"]
                )
                S = S / (1.0 + S / max(s0, 1e-6))
            x = np.append(x, lf * S)
        if self.p["stack_dq"]:
            # A DQ marks a team whose later output is below its filter estimate. The feature
            # harmed playoff Brier on DEV, so it is 0 in playoffs.
            is_qm = (comp_level or "qm") == "qm"
            x = np.append(x, self._dq_feat(red, blue) if is_qm else 0.0)
        if self.p["stack_po"]:
            is_po = 0.0 if (comp_level or "qm") == "qm" else 1.0
            rb_diff = float(rank[1]) if rank is not None else 0.0
            u_diff = float(feats[1] - feats[3]) if feats is not None else 0.0
            x = np.concatenate(
                [x, np.array([is_po * rb_diff, is_po * u_diff, is_po * pcg_r])]
            )
        if not self.p["stack"]:
            return p_h, x
        return self.stacker.prob(x), x

    def _dq_feat(self, red: Sequence[str], blue: Sequence[str]) -> float:
        """Red - blue sum of shrunk team DQ rates, in units of 0.05."""
        k, r0 = float(self.p["dq_k"]), float(self.p["dq_r0"])

        def tot(teams: Sequence[str]) -> float:
            out = 0.0
            for t in teams:
                d, c = self.dq_t.get(t, (0.0, 0.0))
                out += (d + k * r0) / (c + k)
            return out

        return (tot(red) - tot(blue)) / 0.05

    def _nev(self, teams: Sequence[str], event_key: str) -> float:
        """Sum over the teams of the number of earlier events this season (before ``event_key``)."""
        tot = 0
        for t in teams:
            nv = self.nevc.get(t)
            if nv is not None:
                tot += nv[0] if nv[1] == event_key else nv[0] + 1
        return float(tot)

    def _score_pred(self, mean: float, sd: float) -> ScorePrediction:
        """Discretized normal on integers >= 0. Mass below 0 goes to 0."""
        sd = max(sd, 0.5)
        hi = int(math.ceil(max(mean, 0.0) + 6.0 * sd)) + 1
        edges = (np.arange(hi + 1) + 0.5 - mean) / sd
        cdf = ndtr(edges)
        probs = np.diff(np.concatenate(([0.0], cdf)))
        probs[-1] += 1.0 - cdf[-1]
        probs = np.clip(probs, 0.0, None)
        return self._score_from_probs(probs / probs.sum())

    def _foul_adj(self, opp: Sequence[str]) -> float:
        """Expected foul points above the season mean that the opponents give (points)."""
        if not (self.p["foul_team"] and self.comp):
            return 0.0
        k = self.p["foul_k"]
        tot = 0.0
        for t in opp:
            sm, n = self.fteam.get(t, (0.0, 0.0))
            tot += sm / (n + k)
        return tot

    def _ss_refresh(self) -> None:
        kn, kp = self.p["sshape_kn"], self.p["sshape_kp"]
        mass = kn * self.sh_norm + self.ss_cur
        if self.ss_pool_n > 0:
            mass = mass + kp * self.ss_pool / self.ss_pool_n
        mass = mass / mass.sum()
        self.ss_cum = np.concatenate(([0.0], np.cumsum(mass)))
        B, w = self.p["shape_B"], self.p["shape_bw"]
        centers = -B + w * (np.arange(len(mass)) + 0.5)
        self.ss_mu = float(
            centers @ mass
        )  # center the shape: it changes only the PMF shape

    def _shape_key(
        self, x: float, is_qm: bool, forecast: bool = False
    ) -> Optional[Tuple[Any, Any]]:
        """E3c bucket of a residual or forecast (None = the global shape).

        A forecast uses the global shape during the first sshape_gmm_cond_guard matches of the
        season (self.n counts alliances, two per match).
        """
        if not self.gmm_b:
            return None
        if forecast and self.n < 2 * int(self.p["sshape_gmm_cond_guard"]):
            return None
        mode = self.p["sshape_gmm_cond"]
        xk = None
        if mode in ("x", "xl"):
            xk = (
                0
                if x < self.p["sshape_gmm_cond_lo"]
                else (2 if x > self.p["sshape_gmm_cond_hi"] else 1)
            )
        return (xk, bool(is_qm) if mode in ("lvl", "xl") else None)

    def _ss_add(self, t: float, key: Optional[Tuple[Any, Any]] = None) -> None:
        B, w = self.p["shape_B"], self.p["shape_bw"]
        i = int((min(max(t, -B + 1e-9), B - 1e-9) + B) / w)
        self.ss_cur[min(max(i, 0), len(self.ss_cur) - 1)] += 1.0
        self.ss_cur_n += 1.0
        self._ss_refresh()
        if self.gmm is not None:
            self.gmm.add(t)
            if key is not None:
                self.gmm_b[key].add(t)

    def _score_emp_probs(
        self, mean: float, sd: float, key: Optional[Tuple[Any, Any]] = None
    ) -> np.ndarray:
        """Probabilities on integers >= 0 of mean + sd * T with the empirical residual CDF of T."""
        sd = max(sd, 0.5)
        B = self.p["shape_B"]
        hi = int(math.ceil(max(mean, 0.0) + B * sd)) + 1
        z = (np.arange(hi + 1) + 0.5 - mean) / sd
        if self.gmm is not None:
            cdf = (self.gmm_b[key] if key is not None else self.gmm).cdf(z)
        else:
            grid = np.linspace(-B, B, len(self.ss_cum))
            cdf = np.interp(z + self.ss_mu, grid, self.ss_cum)
        probs = np.diff(np.concatenate(([0.0], cdf)))
        probs[-1] += 1.0 - cdf[-1]
        probs = np.clip(probs, 0.0, None)
        return probs / probs.sum()

    def _score_emp(
        self, mean: float, sd: float, key: Optional[Tuple[Any, Any]] = None
    ) -> ScorePrediction:
        """PMF on integers >= 0 from mean + sd * T with the empirical residual CDF of T."""
        return self._score_from_probs(self._score_emp_probs(mean, sd, key))

    def _struct_arms(
        self,
        mean: float,
        sd: float,
        teams: Sequence[str],
        is_po: bool,
        key: Optional[Tuple[Any, Any]] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """(e3, e2cb) probabilities of one alliance. e2cb is None before the structure is ready."""
        pe = self._score_emp_probs(mean, sd, key)
        assert self.struct is not None
        return pe, self.struct.arms(pe, teams, is_po, mean, sd)

    def _score_cal_shift(self, x: float) -> float:
        """Calibrated mean shift in sigma units for a standardized deviation x."""
        n, sx, sxx, se, sxe = self.sc
        ka, kc = self.p["score_cal_ka"], self.p["score_cal_kc"]
        A = np.array([[n + ka, sx], [sx, sxx + kc]])
        a, c = np.linalg.solve(A, np.array([se, sxe]))
        return float(a + c * x)

    def _var_mult(self, x: float) -> float:
        """PMF sd multiplier sqrt(c0 + c1 x) for a standardized mean deviation x."""
        if not self.p["var_cal"]:
            return 1.0
        n, sx, sxx, sq, sxq = self.vc
        k = self.p["var_cal_k"]
        A = np.array([[n + k, sx], [sx, sxx + k]])
        c0, c1 = np.linalg.solve(A, np.array([sq + k, sxq]))
        return math.sqrt(max(float(c0 + c1 * x), self.p["var_cal_floor"]))

    def _score_from_probs(self, probs: np.ndarray) -> ScorePrediction:
        if self.p["lattice"]:
            probs = probs * self.lat_w[np.arange(len(probs)) % len(self.lat_w)]
            probs = probs / probs.sum()
        pmf = PMF.from_array(probs, offset=0, validate=False)
        point = float(probs @ np.arange(len(probs)))
        return ScorePrediction.from_pmf(pmf, point_estimate=point, validate=False)

    def _rp_keys(self) -> Tuple[str, ...]:
        if self.season is None or self.season < 2016:
            return ()
        return ("rp_1", "rp_2", "rp_3") if self.season >= 2025 else ("rp_1", "rp_2")

    def _rp_x(
        self,
        feats: Tuple[float, ...],
        nr: int,
        nb: int,
        po: Tuple[float, float] = (0.0, 0.0),
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Bonus RP features per alliance: [1, own shared, own robot, opponent total] / sigma.

        ``po`` holds the event-progress offsets (points) of red and blue. With ``prog_rp``,
        they shift the shared parts.
        """
        sr, ur, sb, ub = feats[:4]
        sig = max(self._sigma(), 1e-6)
        gam = self._gamma()
        pr, pb = (po[0] / sig, po[1] / sig) if self.p["prog_rp"] else (0.0, 0.0)
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

    def _rp_x_rank(
        self, x_r: np.ndarray, x_b: np.ndarray, feats: Tuple[float, ...]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """With ``rp_agg``, append the own-alliance rank features (top and bottom minus mean)."""
        if not self.p["rp_agg"]:
            return x_r, x_b
        return np.concatenate([x_r, feats[8:10]]), np.concatenate([x_b, feats[10:12]])

    def _rb_z_map(
        self, teams: Sequence[str], h: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, float]]:
        """Standardized team skill (``_prior_z_scalar`` / prior team sd) for the SumChannel cold start.

        The rulebook channels use it only for a team without channel data this season.
        """
        if float(self.p["rb_z_prior"]) <= 0.0:
            return None
        hyp = h if h is not None else self._hyper()
        S0 = self._prior_cov(hyp)
        sd0 = math.sqrt(max(float((S0 @ np.ones(2)).sum()), 1e-6))
        return {t: self._prior_z_scalar(t, hyp) / sd0 for t in teams}

    def _rp_bonus(
        self,
        keys: Sequence[str],
        x: np.ndarray,
        tier: str,
        teams: Sequence[str],
        opp: Sequence[str],
    ) -> Dict[str, float]:
        """Bonus RP probabilities per key: the rulebook model, else the logistic fallback."""
        bon = self.bonus.probs(keys, x[:4])
        if self.p["rp_rule"] and self.rbonus.supported():
            z_map = self._rb_z_map(list(teams) + list(opp))
            rule = self.rbonus.probs(keys, tier, teams, opp, extra=x[1:], z_map=z_map)
            bon = {k: (bon[k] if rule.get(k) is None else rule[k]) for k in keys}
        return bon

    def _tier(
        self, event_key: str, event_type: Optional[int], count: bool = False
    ) -> str:
        """Event tier from the TBA event_type (source of truth), else from the key.

        With ``count`` (update only), a fallback to the key is counted per match and
        logged once per event. predict_match must not write state, so it does not count.
        """
        if event_type is None and count:
            self.tier_fallbacks += 1
            if event_key not in self.tier_fallback_events:
                self.tier_fallback_events.add(event_key)
                logger.info(
                    "hkf: no event_type for %s, tier from the event key", event_key
                )
        return tier_of(event_key, event_type)

    def _rp_pred(
        self,
        p_win: float,
        x: np.ndarray,
        tier: str,
        teams: Sequence[str],
        opp: Sequence[str],
    ) -> Optional[RankingPointsPrediction]:
        keys = self._rp_keys()
        if not keys:
            return None
        bon = self._rp_bonus(keys, x, tier, teams, opp)
        wv, tv = rp_values(self.season)
        max_rp = float(wv + len(keys))
        # p_win counts a tie as half a win: P(W) = p - P(T)/2. The mean RP is
        # wv P(W) + tv P(T) + sum q = wv p + (tv - wv/2) P(T) + sum q. For wv 2 and tv 1
        # the tie term is exactly 0, so the pre-2025 value is wv p + sum q.
        pw, pt, _ = self.rpj.outcome_probs(p_win)
        exp = min(
            max_rp, max(0.0, wv * p_win + (tv - 0.5 * wv) * pt + sum(bon.values()))
        )
        median = None
        if self.p["rp_median"]:
            # Median of the joint RP PMF (win and tie RP values, correlated bonuses).
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
        """Per-season rank weights [own top, own bottom, opp top, opp bottom] (ridge, pooled prior)."""
        dim = 4 if self.p["agg_opp"] else 2
        out = np.zeros(4)
        if not self.p["agg"]:
            return out
        k = self.p["agg_k"]
        a0 = self.ag_prior[:dim]
        A = self.ag_xx[:dim, :dim] + k * np.eye(dim)
        out[:dim] = np.linalg.solve(A, self.ag_xe[:dim] + k * a0)
        return out

    @staticmethod
    def _rank_x(s: np.ndarray, t: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """Centered top and bottom shared strengths. Rank by total strength t. Returns (x, i_top, i_bot)."""
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
        """Weights on the shared strengths of one alliance: 1 + a_top (1[top] - 1/n) + a_bot (1[bot] - 1/n)."""
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
        if self.p["agg"]:
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
        """Per-alliance rank structure: [red top - mean, red bottom - mean, blue top - mean, blue bottom - mean]."""
        t = mu[0::2] + mu[1::2]
        out = np.zeros(4)
        for j, a in enumerate((t[:nr], t[nr:])):
            if len(a) >= 2:
                out[2 * j] = float(a.max() - a.mean())
                out[2 * j + 1] = float(a.min() - a.mean())
        return out

    @staticmethod
    def _sorted_s(mu: np.ndarray, nr: int) -> np.ndarray:
        """Shared strengths sorted by descending total strength for 3-team red and blue alliances."""
        s = mu[0::2]
        t = s + mu[1::2]
        out = np.zeros(6)
        for j, (s_a, t_a) in enumerate(((s[:nr], t[:nr]), (s[nr:], t[nr:]))):
            if len(s_a) == 3:
                ord_i = np.argsort(-t_a, kind="stable")
                out[3 * j : 3 * j + 3] = s_a[ord_i]
        return out

    def _refresh_sat_w(self) -> None:
        """Recompute online ridge weights for po_score_cal (0:2) and rank_score_cal (2:6)."""
        if not (self.p["po_score_cal"] or self.p["rank_score_cal"]):
            self.sat_w = np.zeros(self.sat_dim)
            return
        k_reg = float(self.p["sat_k"])
        A = self.sat_xx_pool + self.sat_xx_cur + k_reg * np.eye(self.sat_dim)
        b = self.sat_xe_pool + self.sat_xe_cur
        w = np.linalg.solve(A, b)
        if not self.p["po_score_cal"]:
            w[0:2] = 0.0
        if not self.p["rank_score_cal"]:
            w[2:6] = 0.0
        self.sat_w = w

    def _sat_feats(
        self,
        ek: str,
        teams: Sequence[str],
        s_ord: Sequence[float],
        z_opp: float,
        is_qm: bool,
    ) -> np.ndarray:
        """Alliance score saturation feature vector in sigma units."""
        x = np.zeros(self.sat_dim)
        if not is_qm and self.p["po_score_cal"]:
            h_po = self.po_res.get((ek, tuple(sorted(teams))))
            po_len = float(len(h_po)) if h_po else 0.0
            x[0] = min(po_len, 6.0) / 6.0
            x[1] = max(0.0, z_opp)
        if len(teams) == 3 and self.p["rank_score_cal"]:
            s1, s2, s3 = float(s_ord[0]), float(s_ord[1]), float(s_ord[2])
            s12 = max(0.0, s1) * max(0.0, s2)
            x[2] = s1 - self.qm_s_mean[0]
            x[3] = s2 - self.qm_s_mean[1]
            x[4] = s3 - self.qm_s_mean[2]
            x[5] = s12 - self.qm_s_mean[3]
        return x

    def _margin(
        self,
        red: Sequence[str],
        blue: Sequence[str],
        event_key: str,
        h: Dict[str, float],
        with_feats: bool = False,
    ) -> Tuple[Any, ...]:
        """Return (mean margin, margin variance, red z, blue z) in sigma units.

        With ``with_feats``, also return (sum s red, sum u red, sum s blue, sum u blue).
        """
        mu, cov = self._view(event_key, list(red) + list(blue), h)
        nr, nb = len(red), len(blue)
        gam = self._gamma()
        # red score z = sum(s+u)_red - gam * sum(s)_blue, and likewise for blue.
        wr, wb = self._alliance_rows(mu, nr, nb, gam)
        hv = wr - wb
        # Foul transfer moves the alliance score means only. In the margin it lowered Brier
        # skill on DEV (ablation log, Phase 3).
        fa_r, fa_b = self._foul_adj(blue), self._foul_adj(red)
        d = float(hv @ mu)
        noise = (
            2.0 * h["rs"] * (1.0 - self.p["noise_corr"])
            + (nr + nb) * h["ru"]
            + 2.0 * h["rf"]
        )
        var = float(hv @ cov @ hv) + noise
        zr_ = float(wr @ mu) + fa_r / self._sigma()
        zb_ = float(wb @ mu) + fa_b / self._sigma()
        if not with_feats:
            return d, var, zr_, zb_
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
            + tuple(self._rank_feats(mu, nr))
            + tuple(self._own_rank(mu, nr))
            + tuple(self._sorted_s(mu, nr))
        )
        return d, var, zr_, zb_, feats

    def _playoff_bonus_forecast(
        self,
        red: Sequence[str],
        blue: Sequence[str],
        feats: Tuple[float, ...],
        po: Tuple[float, float],
        event_key: str,
        event_type: Optional[int],
    ) -> Tuple[float, float, float, float]:
        """Expected 2016/2017 playoff threshold bonus points and variances for red and blue."""
        if self.season not in (2016, 2017):
            return 0.0, 0.0, 0.0, 0.0
        x_r, x_b = self._rp_x_rank(*self._rp_x(feats, len(red), len(blue), po), feats)
        tier = self._tier(event_key, event_type)
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
        self, event_key: str, red: Sequence[str], blue: Sequence[str], is_qm: bool
    ) -> Tuple[float, float]:
        """Shrunken pre-match standardized playoff residual for fixed red and blue alliances."""
        if is_qm or not self.p["playoff_synergy"]:
            return 0.0, 0.0
        k = float(self.p["po_syn_k"])
        hr = self.po_res.get((event_key, tuple(sorted(red))))
        hb = self.po_res.get((event_key, tuple(sorted(blue))))
        sr = float(sum(hr)) / (len(hr) + k) if hr else 0.0
        sb = float(sum(hb)) / (len(hb) + k) if hb else 0.0
        return sr, sb

    def _score_ms(
        self,
        red: Sequence[str],
        blue: Sequence[str],
        ek: str,
        is_qm: bool,
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
        mr = self._level_parts(len(red)) + sig * zr + eb[0]
        mb = self._level_parts(len(blue)) + sig * zb + eb[1]
        if self.p["score_cal"]:
            mr += sig * self._score_cal_shift(zr)
            mb += sig * self._score_cal_shift(zb)
        mr += po[0] + sig * float(self.p["po_syn_s"]) * sy[0]
        mb += po[1] + sig * float(self.p["po_syn_s"]) * sy[1]
        if self.p["po_score_cal"] or self.p["rank_score_cal"]:
            mr += sig * float(
                self.sat_w @ self._sat_feats(ek, red, feats[12:15], zb, is_qm)
            )
            mb += sig * float(
                self.sat_w @ self._sat_feats(ek, blue, feats[15:18], zr, is_qm)
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
        h = self._hyper()
        d, var, zr, zb, feats = self._margin(
            red, blue, context.event_key, h, with_feats=True
        )
        sig = self._sigma()
        is_qm = (context.comp_level or "qm") == "qm"
        meta = context.event_metadata or {}
        ev_type = meta.get("event_type")
        po_r, po_b = self._prog_off(context.event_key, red), self._prog_off(
            context.event_key, blue
        )
        eb_r = eb_b = 0.0
        eb_vr = eb_vb = 0.0
        if self.p["playoff_bonus"] and not is_qm and self.season in (2016, 2017):
            eb_r, eb_b, eb_vr, eb_vb = self._playoff_bonus_forecast(
                red, blue, feats, (po_r, po_b), context.event_key, ev_type
            )
            d += (eb_r - eb_b) / sig
            var += (eb_vr + eb_vb) / (sig * sig)
        sy_r, sy_b = self._po_synergy(context.event_key or "", red, blue, is_qm)
        d += float(self.p["po_syn_d"]) * (sy_r - sy_b)
        p, _ = self._final_prob(
            self._win_prob(d / math.sqrt(max(var, 1e-9))),
            red,
            blue,
            self._stack_rank(feats),
            context.event_key,
            feats,
            h,
            zs=(zr, zb),
            comp_level=context.comp_level,
        )
        p = min(1.0, max(0.0, p))
        mr, mb, sd_r, sd_b = self._score_ms(
            red,
            blue,
            context.event_key or "",
            is_qm,
            sig,
            feats,
            zr,
            zb,
            (po_r, po_b),
            (eb_r, eb_b),
            (eb_vr, eb_vb),
            (sy_r, sy_b),
        )
        kr = self._shape_key(
            (mr - eb_r - self._level_parts(len(red))) / sig, is_qm, forecast=True
        )
        kb = self._shape_key(
            (mb - eb_b - self._level_parts(len(blue))) / sig, is_qm, forecast=True
        )
        if self.p["pmf"]:
            if self.p["sshape"] and self.struct is not None:
                red_score = self._score_from_probs(
                    self.struct.mix(*self._struct_arms(mr, sd_r, red, not is_qm, kr))
                )
                blue_score = self._score_from_probs(
                    self.struct.mix(*self._struct_arms(mb, sd_b, blue, not is_qm, kb))
                )
            elif self.p["sshape"]:
                red_score = self._score_emp(mr, sd_r, kr)
                blue_score = self._score_emp(mb, sd_b, kb)
            else:
                red_score = self._score_pred(mr, sd_r)
                blue_score = self._score_pred(mb, sd_b)
        else:
            red_score = ScorePrediction.from_point(max(0.0, mr))
            blue_score = ScorePrediction.from_point(max(0.0, mb))
        red_rp = blue_rp = None
        if self.p["rp"] and context.comp_level == "qm":
            x_r, x_b = self._rp_x_rank(
                *self._rp_x(feats, len(red), len(blue), (po_r, po_b)), feats
            )
            tier = self._tier(context.event_key, ev_type)
            red_rp = self._rp_pred(p, x_r, tier, red, blue)
            blue_rp = self._rp_pred(1.0 - p, x_b, tier, blue, red)
        return MatchPrediction(
            red_win_prob=p,
            red_score=red_score,
            blue_score=blue_score,
            red_rp=red_rp,
            blue_rp=blue_rp,
        )

    def update(self, outcome: MatchOutcome) -> None:
        """Learn from one played match. Every learner trains on the pre-match forecast inputs."""
        if (
            hasattr(self, "processed_match_keys")
            and outcome.match_key in self.processed_match_keys
        ):
            return
        red = list(outcome.red_teams)
        blue = list(outcome.blue_teams)
        if not red or not blue:
            return
        h = self._hyper()
        sig = self._sigma()
        ek = outcome.event_key or ""
        is_qm = (outcome.comp_level or "qm") == "qm"
        ev_type = getattr(outcome, "event_type", None)
        # Preseason match under w0_mode: season statistics only (plus team state for "team").
        w0 = self.p["w0_mode"] != "off" and ev_type == 100
        # Pre-update forecast quantities. Compute them all before any state changes
        # so that every online learner trains on the same inputs predict_match used.
        d, var, zr, zb, feats = self._margin(red, blue, ek, h, with_feats=True)
        pre_po = (self._prog_off(ek, red), self._prog_off(ek, blue))
        pre_pb = (self._prog_bin(ek, red), self._prog_bin(ek, blue))
        eb_r = eb_b = 0.0
        eb_vr = eb_vb = 0.0
        if self.p["playoff_bonus"] and not is_qm and self.season in (2016, 2017):
            eb_r, eb_b, eb_vr, eb_vb = self._playoff_bonus_forecast(
                red, blue, feats, pre_po, ek, ev_type
            )
            d += (eb_r - eb_b) / sig
            var += (eb_vr + eb_vb) / (sig * sig)
        pre_sy = self._po_synergy(ek, red, blue, is_qm)
        # Score structure: the (e3, e2cb) PMFs that predict_match mixed, from the pre-match state.
        pre_struct = None
        if self.struct is not None and self.p["pmf"] and self.p["sshape"] and not w0:
            mr_s, mb_s, sdr_s, sdb_s = self._score_ms(
                red,
                blue,
                ek,
                is_qm,
                sig,
                feats,
                zr,
                zb,
                pre_po,
                (eb_r, eb_b),
                (eb_vr, eb_vb),
                pre_sy,
            )
            kr_s = self._shape_key(
                (mr_s - eb_r - self._level_parts(len(red))) / sig, is_qm, forecast=True
            )
            kb_s = self._shape_key(
                (mb_s - eb_b - self._level_parts(len(blue))) / sig, is_qm, forecast=True
            )
            pre_struct = (
                self._struct_arms(mr_s, sdr_s, red, not is_qm, kr_s),
                self._struct_arms(mb_s, sdb_s, blue, not is_qm, kb_s),
            )
        p_h = self._win_prob(d / math.sqrt(max(var, 1e-9)))
        p_pre, x_stack = self._final_prob(
            p_h,
            red,
            blue,
            self._stack_rank(feats),
            ek,
            feats,
            h,
            zs=(zr, zb),
            comp_level=outcome.comp_level,
        )
        p_pre = min(1.0, max(0.0, p_pre))
        x_rp_red, x_rp_blue = self._rp_x_rank(
            *self._rp_x(feats, len(red), len(blue), pre_po), feats
        )
        rp_keys = self._rp_keys()
        pre_bon = None
        tr = None
        if self.p["rp"] and rp_keys and is_qm and not w0:
            # The same event tier as predict_match: TBA event_type, else the key (counted).
            tr = self._tier(ek, ev_type, count=True)
            # Pre-update bonus probabilities, as in predict_match. The joint RP model
            # (tie rate and rho) trains on them. expected_rp uses the tie rate, so it
            # trains even when rp_median is off.
            pre_bon = (
                self._rp_bonus(rp_keys, x_rp_red, tr, red, blue),
                self._rp_bonus(rp_keys, x_rp_blue, tr, blue, red),
            )
        bd = outcome.score_breakdown or {}
        pb_r = (
            playoff_bonus_points(
                self.season, bd.get("red") if isinstance(bd, dict) else None, is_qm
            )
            if self.p["playoff_bonus"]
            else 0.0
        )
        pb_b = (
            playoff_bonus_points(
                self.season, bd.get("blue") if isinstance(bd, dict) else None, is_qm
            )
            if self.p["playoff_bonus"]
            else 0.0
        )
        # MatchOutcome validates both scores as non-negative ints and always sets actual_red_win.
        rsc_clean = float(outcome.red_score) - pb_r
        bsc_clean = float(outcome.blue_score) - pb_b
        e_m = (float(outcome.red_score) - float(outcome.blue_score)) / sig - d
        y_win = float(outcome.actual_red_win)

        if self.p["shape"] == "emp" and self.n > 0 and not w0:
            self._shape_add(e_m / math.sqrt(max(var, 1e-9)))
        pre_shift = (
            self._score_cal_shift(zr) if self.p["score_cal"] else 0.0,
            self._score_cal_shift(zb) if self.p["score_cal"] else 0.0,
        )
        if (self.p["po_score_cal"] or self.p["rank_score_cal"]) and not w0:
            x_sat_r = self._sat_feats(ek, red, feats[12:15], zb, is_qm)
            x_sat_b = self._sat_feats(ek, blue, feats[15:18], zr, is_qm)
            pre_sat = (float(self.sat_w @ x_sat_r), float(self.sat_w @ x_sat_b))
            if self.n > 0:
                base_r = (
                    self._level_parts(len(red))
                    + sig * (zr + pre_shift[0])
                    + pre_po[0]
                    + sig * float(self.p["po_syn_s"]) * pre_sy[0]
                )
                base_b = (
                    self._level_parts(len(blue))
                    + sig * (zb + pre_shift[1])
                    + pre_po[1]
                    + sig * float(self.p["po_syn_s"]) * pre_sy[1]
                )
                delta_sat = float(self.p["sat_huber"])
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
            if self.p["rank_score_cal"] and is_qm and len(red) == 3 and len(blue) == 3:
                for sr_s in (feats[12:15], feats[15:18]):
                    vec = np.array(
                        [
                            sr_s[0],
                            sr_s[1],
                            sr_s[2],
                            max(0.0, sr_s[0]) * max(0.0, sr_s[1]),
                        ]
                    )
                    self.qm_s_n += 1.0
                    w_qm = max(1.0 / self.qm_s_n, 1.0 / 2000.0)
                    self.qm_s_mean += w_qm * (vec - self.qm_s_mean)
        if not is_qm and self.p["playoff_synergy"] and not w0:
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
        if (
            (self.p["sshape"] or self.p["score_cal"] or self.p["var_cal"])
            and self.n > 0
            and not w0
        ):
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
                if self.p["sshape"]:
                    self._ss_add(
                        (float(y_a) - m_a) / (sd_a * vm_a), self._shape_key(x_a, is_qm)
                    )
                if self.p["var_cal"]:
                    q = ((float(y_a) - m_a) / sd_a) ** 2
                    self.vc = self.p["var_cal_decay"] * self.vc + np.array(
                        [1.0, x_a, x_a * x_a, q, x_a * q]
                    )

                if self.p["score_cal"]:
                    # Fit against the mean of the normal truncated at 0 (close to the PMF mean).
                    loc = self._level_parts(n_a) + sig * z_a
                    s_a = max(sig * math.sqrt(max(v_a, 1e-9)), 0.5)
                    r_ = loc / s_a
                    loc = loc * _phi(r_) + s_a * math.exp(-0.5 * r_ * r_) / math.sqrt(
                        2.0 * math.pi
                    )
                    e_a = (float(y_a) - po - loc) / sig
                    self.sc = self.p["score_cal_decay"] * self.sc + np.array(
                        [1.0, z_a, z_a * z_a, e_a, z_a * e_a]
                    )
        if self.p["prog_off"] and self.n > 0 and (not w0 or self.p["w0_prog"]):
            for z_a, n_a, y_a, shift, b in (
                (zr, len(red), rsc_clean, pre_shift[0], pre_pb[0]),
                (zb, len(blue), bsc_clean, pre_shift[1], pre_pb[1]),
            ):
                r_a = float(y_a) - (self._level_parts(n_a) + sig * (z_a + shift))
                self.pg_cur[0, b] += r_a / sig
                self.pg_cur[1, b] += 1.0
        if self.p["lattice"] and not w0:
            P = len(self.lat_cnt)
            for y_a in (outcome.red_score, outcome.blue_score):
                self.lat_cnt[int(y_a) % P] += 1.0
            a = self.p["lat_a"]
            self.lat_w = P * (self.lat_cnt + a) / (self.lat_cnt.sum() + P * a)
        if pre_struct is not None and self.struct is not None:
            self.struct.learn(
                [
                    (pre_struct[0][0], pre_struct[0][1], int(outcome.red_score)),
                    (pre_struct[1][0], pre_struct[1][1], int(outcome.blue_score)),
                ]
            )
            bd_s = (
                outcome.score_breakdown
                if isinstance(outcome.score_breakdown, dict)
                else {}
            )
            self.struct.observe(
                red, not is_qm, bd_s.get("red"), float(outcome.red_score)
            )
            self.struct.observe(
                blue, not is_qm, bd_s.get("blue"), float(outcome.blue_score)
            )
        if self.p["stack"] and not w0:
            self.stacker.update(x_stack, y_win)
            g = self.p["elo_k"] * (y_win - 1.0 / (1.0 + math.exp(-x_stack[1])))
            for t in red:
                self.wr[t] = (self._wr_get(t) + g, self.season)
            for t in blue:
                self.wr[t] = (self._wr_get(t) - g, self.season)
        # Preseason matches do not count as team experience (event and match counts).
        for t in (red + blue if not w0 else ()):
            nv = self.nevc.get(t)
            if nv is None:
                self.nevc[t] = (0, ek)
            elif nv[1] != ek:
                self.nevc[t] = (nv[0] + 1, ek)
            self.scount[t] = self.scount.get(t, 0) + 1
            self.ecount[(ek, t)] = self.ecount.get((ek, t), 0) + 1
        if w0 and self.p["w0_prog"]:
            # E1d: within-event counts of the week-0 event place its residuals in the right
            # progress bin. The key includes the event, so no regular event reads them.
            for t in red + blue:
                self.ecount[(ek, t)] = self.ecount.get((ek, t), 0) + 1
        if pre_bon is not None:
            # Train the joint RP PMF on the pre-match forecast: the tie rate once per match,
            # rho_k once per alliance with bonus labels.
            self.rpj.update_tie(p_pre, y_win == 0.5)
            res_red = "W" if y_win == 1.0 else ("L" if y_win == 0.0 else "T")
            res_blue = {"W": "L", "L": "W", "T": "T"}[res_red]
            for p_a, bon_a, res_a, labels in (
                (p_pre, pre_bon[0], res_red, outcome.red_bonus_rps),
                (1.0 - p_pre, pre_bon[1], res_blue, outcome.blue_bonus_rps),
            ):
                if isinstance(labels, dict) and labels:
                    self.rpj.update_bonus(
                        p_a, bon_a, res_a, {k: labels.get(k) for k in rp_keys}
                    )
        # (rp or po) and (qm or po) reduces to po or (rp and qm).
        po_season = bool(self.p["playoff_bonus"]) and self.season in (2016, 2017)
        if rp_keys and (po_season or (self.p["rp"] and is_qm)) and not w0:
            if is_qm:
                for x_rp, labels in (
                    (x_rp_red, outcome.red_bonus_rps),
                    (x_rp_blue, outcome.blue_bonus_rps),
                ):
                    if isinstance(labels, dict) and labels:
                        self.bonus.update(
                            {k: v for k, v in labels.items() if k in rp_keys}, x_rp[:4]
                        )
            bd_all = (
                outcome.score_breakdown
                if isinstance(outcome.score_breakdown, dict)
                else {}
            )
            if self.p["rp_rule"] and self.rbonus.supported() and bd_all:
                self.rbonus.update(
                    tr if tr is not None else self._tier(ek, ev_type),
                    red,
                    blue,
                    bd_all.get("red") or {},
                    bd_all.get("blue") or {},
                    (outcome.red_bonus_rps or {}) if is_qm else {},
                    (outcome.blue_bonus_rps or {}) if is_qm else {},
                    x_rp_red[1:],
                    x_rp_blue[1:],
                    z_map=self._rb_z_map(red + blue, h),
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
        w_pcg = 1.0 if is_qm else (float(self.p["pcg_po_w"]) if self.n > 0 else 0.0)
        if w0:
            w_pcg = 0.0
        if w_pcg > 0.0 and len(red) == 3 and len(blue) == 3 and self.p["cross_pcg"]:
            self.pcg_cnt += 1
            reg = float(self.p["pcg_reg"])
            step = max(1, int(self.p["pcg_step"]))
            gam_pcg = self._gamma()
            fa_r, fa_b = self._foul_adj(blue), self._foul_adj(red)
            lvl3 = self._level_parts(3)
            po_pcg_r = pre_po[0] if self.p["pcg_prog_debias"] else 0.0
            po_pcg_b = pre_po[1] if self.p["pcg_prog_debias"] else 0.0
            z_r = (rsc_clean - lvl3 - po_pcg_r - fa_r) / sig + gam_pcg * feats[2]
            z_b = (bsc_clean - lvl3 - po_pcg_b - fa_b) / sig + gam_pcg * feats[0]
            if self.p["event_pcg"]:
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
            else:
                for teams, z_obs in ((red, z_r), (blue, z_b)):
                    for t in teams:
                        if t not in self.s_atb:
                            z0 = self._prior_z_scalar(t, h)
                            self.s_atb[t] = reg * z0
                            self.pcg_z[t] = z0
                        self.s_atb[t] += w_pcg * z_obs
                        row_t = self.s_ata.setdefault(t, {})
                        for u in teams:
                            row_t[u] = row_t.get(u, 0.0) + w_pcg
                if self.pcg_cnt % step == 0:
                    self.pcg_z = _solve_pcg_dict(
                        self.s_ata, self.s_atb, reg, self.pcg_z, iters=5
                    )
        sides = []
        for side, teams, total in (("red", red, rsc_clean), ("blue", blue, bsc_clean)):
            rp = fp = None
            if self.comp and isinstance(bd, dict):
                rp = robot_points(self.season, bd.get(side), len(teams))
                fp = foul_points(bd.get(side))
            sides.append((teams, float(total), rp, fp))

        rows: List[np.ndarray] = []
        ys: List[float] = []
        kinds: List[str] = []
        gam = self._gamma()
        agg = bool(self.p["agg"])
        a_c = self._agg_coef() if agg else None
        ag_upd: List[Tuple[np.ndarray, float]] = []
        opp_of = {0: 1, 1: 0}
        for j_side, (teams, total, rp, fp) in enumerate(sides):
            idx = [es.idx[t] for t in teams]
            oidx = [es.idx[t] for t in sides[opp_of[j_side]][0]]
            if agg:
                # Rank weights at the pre-update means (extended Kalman filter linearization).
                s_o, s_p = mu[idx], mu[oidx]
                t_o, t_p = (
                    s_o + mu[[i + 1 for i in idx]],
                    s_p + mu[[i + 1 for i in oidx]],
                )
                w_own = self._agg_w(s_o, t_o, a_c[0], a_c[1])
                w_opp = self._agg_w(s_p, t_p, a_c[2], a_c[3]) - 1.0 - gam
                x_ag = np.concatenate(
                    [self._rank_x(s_o, t_o)[0], self._rank_x(s_p, t_p)[0]]
                )
            po_debias = (pre_po[j_side] / sig) if self.p["prog_filter_debias"] else 0.0
            if self.comp and rp is not None and fp is not None:
                hrow = np.zeros(n)
                hrow[idx] = 1.0
                hrow[oidx] = -gam
                if agg:
                    hrow[idx] = w_own
                    hrow[oidx] = w_opp
                shared = total - fp - sum(rp)
                rows.append(hrow)
                yv = (shared - self.Ls) / sig - po_debias
                ys.append(yv)
                kinds.append("s")
                if self.p["interaction"] and not w0:
                    x = -float(mu[oidx].sum())
                    e0 = yv - float(mu[idx].sum())
                    self.g_xy += x * e0
                    self.g_xx += x * x
                if agg:
                    ag_upd.append(
                        (x_ag, yv - float(mu[idx].sum()) + gam * float(mu[oidx].sum()))
                    )
                for i, pts in zip(idx, rp):
                    hr = np.zeros(n)
                    hr[i + 1] = 1.0
                    rows.append(hr)
                    ys.append((pts - self.Lu) / sig)
                    kinds.append("u")
            else:
                hrow = np.zeros(n)
                hrow[idx] = 1.0
                hrow[[i + 1 for i in idx]] = 1.0
                hrow[oidx] = -gam
                if agg:
                    hrow[idx] = w_own
                    hrow[oidx] = w_opp
                rows.append(hrow)
                yv = (total - self._level_parts(len(teams))) / sig - po_debias
                ys.append(yv)
                kinds.append("t")
                if self.p["interaction"] and not w0:
                    x = -float(mu[oidx].sum())
                    e0 = yv - float(mu[idx].sum() + mu[[i + 1 for i in idx]].sum())
                    self.g_xy += x * e0
                    self.g_xx += x * x
                if agg:
                    e_l = (
                        yv
                        - float(mu[idx].sum() + mu[[i + 1 for i in idx]].sum())
                        + gam * float(mu[oidx].sum())
                    )
                    ag_upd.append((x_ag, e_l))
        if w0:
            ag_upd = []
        if self.p["agg_diff"]:
            if len(ag_upd) == 2:
                dx = ag_upd[0][0] - ag_upd[1][0]
                de = ag_upd[0][1] - ag_upd[1][1]
                self.ag_xx += np.outer(dx, dx)
                self.ag_xe += dx * de
        else:
            for x_ag, e_l in ag_upd:
                self.ag_xx += np.outer(x_ag, x_ag)
                self.ag_xe += x_ag * e_l
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
            R[a, b] = R[b, a] = self.p["noise_corr"] * math.sqrt(R[a, a] * R[b, b])
        if w0 and self.p["w0_mode"] == "team":
            R = R * float(self.p["w0_k"])
        PHt = cov @ H.T
        HPH = H @ PHt
        S = HPH + R
        e = y - H @ mu
        rc = self.p["robust_c"]
        if rc > 0:
            # Huber weights on the shared/total rows: an innovation beyond rc standard
            # deviations gets the effective variance S_jj * |r| / rc.
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
        qm = self.p["q_match"]
        if qm > 0:
            # Team strength drifts between matches: add process noise to the teams that played.
            S0 = self._prior_cov(h)
            for t in red + blue:
                i = es.idx[t]
                cov[i : i + 2, i : i + 2] += qm * S0
        # "stats" mode: the preseason event state stays private. No team state leaves it.
        for t in (red + blue if not w0 or self.p["w0_mode"] == "team" else ()):
            i = es.idx[t]
            self.teams[t] = (
                mu[i : i + 2].copy(),
                cov[i : i + 2, i : i + 2].copy(),
                self.season,
                ek,
            )

        # ---- season statistics (all in points)
        lp = self.p
        for teams, total, rp, fp in sides:
            self.n += 1
            self.tot.add(
                total,
                lp["level_prior_n"],
                lp["level_min_w"],
                lp["var_prior_n"],
                lp["var_min_w"],
            )
        w = max(1.0 / (self.n + lp["level_prior_n"]), lp["level_min_w"])
        for j, k in enumerate(kinds):
            ep = e[j] * sig
            mv = HPH[j, j] * sig * sig
            if k == "s":
                self.Ls += w * ep
                self.rs_sum += ep * ep - mv
                self.rs_n += 1
            elif k == "u":
                self.nu += 1
                wu = max(1.0 / (self.nu + lp["level_prior_n"]), lp["level_min_w"])
                self.Lu += wu * ep
                self.ru_sum += ep * ep - mv
                self.ru_n += 1
            else:
                self.Ls += w * ep
        if self.p["foul_team"] and self.comp and not w0:
            fmean = self.foul.mean
            for j_side, (teams, total, rp, fp) in enumerate(sides):
                if fp is None:
                    continue
                opp = sides[opp_of[j_side]][0]
                dev = (fp - fmean) / max(len(opp), 1)
                for t in opp:
                    sm, n = self.fteam.get(t, (0.0, 0.0))
                    self.fteam[t] = (sm + dev, n + 1.0)
        for teams, total, rp, fp in sides:
            if self.comp and rp is not None and fp is not None:
                self.foul.add(
                    fp,
                    lp["level_prior_n"],
                    lp["level_min_w"],
                    lp["var_prior_n"],
                    lp["var_min_w"],
                )
                self.sh.add(
                    total - fp - sum(rp),
                    lp["level_prior_n"],
                    0.0,
                    lp["var_prior_n"],
                    0.0,
                )
                for pts in rp:
                    self.rob.add(pts, lp["level_prior_n"], 0.0, lp["var_prior_n"], 0.0)
        # ---- DQ-rate statistics for stack_dq (written after every forecast input above is fixed)
        if self.p["stack_dq"] and not w0:
            for teams, dqs in ((red, outcome.red_dqs), (blue, outcome.blue_dqs)):
                dq_set = set(dqs or ())
                for t in teams:
                    d, c = self.dq_t.get(t, (0.0, 0.0))
                    self.dq_t[t] = (d + (1.0 if t in dq_set else 0.0), c + 1.0)
        if hasattr(self, "processed_match_keys"):
            self.processed_match_keys.add(outcome.match_key)


class HKFEventPCGPredictor(HKFPredictor):
    """HKF predictor with Two-Level Staged Per-Event PCG and high-scoring/playoff calibration enabled by default.

    The score lattice (`lattice`, a learned `y mod 10` weighting) is off. It fits only some
    games, and this model targets structure that holds in every season. In its place, the
    rules-free score structure (`score_struct`) learns the score steps of each game from the
    breakdown fields. `scale_fix_pmf` sets the score PMF width from the centered season
    variance. `sshape_gmm` replaces the 0.05-sd bins of the learned residual shape with an
    online 5-component Gaussian mixture (with its own small prior weights). Evidence:
    docs/experiments/ (tracked DEV runs; E3-gmm in docs/experiments/e3_gmm.md). `sshape_gmm_cond`
    fits one mixture per match bucket (E3c, docs/experiments/e3c_conditional_shape.md).
    Clean-slate pruning and tuning (`docs/experiments/clean_slate/`) disables `pcg_prog_debias`
    and `stack_early`, and sets `pcg_reg=16.0`, `drift_event=0.17`, and `pcg_ev_carry=0.40`.
    """

    is_standalone: bool = True
    external_dependencies: Tuple[str, ...] = ()

    def __init__(self, name: str = "hkf_ev_pcg", **params: Any) -> None:
        params.setdefault("event_pcg", True)
        params.setdefault("stack_lvl_sat", True)
        params.setdefault("stack_po", True)
        params.setdefault("po_score_cal", True)
        params.setdefault("rank_score_cal", True)
        params.setdefault("lattice", False)
        params.setdefault("score_struct", True)
        params.setdefault("scale_fix_pmf", True)
        params.setdefault("sshape_gmm", True)
        # E3c conditional shape: one GMM per (qual/playoff, score level) bucket, global shape for
        # the first 500 matches of each season (docs/experiments/e3c_conditional_shape.md).
        params.setdefault("sshape_gmm_cond", "xl")
        params.setdefault("sshape_gmm_cond_kg", 2000.0)
        params.setdefault("sshape_gmm_cond_guard", 500)
        # Clean-slate Stage 3 & 4 pruning and tuning (docs/experiments/clean_slate/, ledger Entry 13).
        params.setdefault("pcg_prog_debias", False)
        params.setdefault("stack_early", 0.0)
        params.setdefault("pcg_reg", 16.0)
        params.setdefault("drift_event", 0.17)
        params.setdefault("pcg_ev_carry", 0.40)
        super().__init__(name=name, **params)
