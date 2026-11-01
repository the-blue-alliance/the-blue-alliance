"""Hyperparameters of the HKF match predictor.

Numerical settings that are not modeling choices (grid widths, supports, bin counts, EM
schedules) are constants in the modules that use them.

The values are the validated configuration (see docs/Developing/Predictions-v2-Model.md).
They are never stored with the model state: a loaded state always runs with the values in
this file.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HKFConfig:
    # ---- Team state and filter dynamics
    team_share: float = 0.6  # prior share of alliance-score variance explained by teams
    rho: float = 0.78  # season-to-season mean carryover of normalized team strength
    rho_v: float = (
        0.75  # season-to-season covariance carryover of normalized team strength
    )
    rookie_z: float = -0.5  # rookie prior mean in units of team sd
    q_event: float = (
        0.05  # process variance added at a new event (fraction of prior cov)
    )
    drift_event: float = 0.17  # mean total z change when a team starts a new event
    q_match: float = 0.003  # process variance (fraction of prior cov) added per match
    noise_corr: float = 0.05  # correlation of red and blue shared-score noise
    robust_c: float = 2.2  # Huber threshold on standardized shared/total innovations
    robot_team_share: float = (
        0.5  # prior share of robot-points variance explained by teams
    )
    kappa: float = 0.5  # prior correlation between shared and robot team strength
    hyper_n: float = 1000.0  # pseudo count for online noise and spread estimates
    gamma_k0: float = 200.0  # shrinkage of the opponent interaction toward 0
    hist_beta: float = (
        0.35  # weight of older seasons' mean strength in the new-season prior
    )
    hist_k: int = 3  # number of older seasons averaged
    level_prior_n: float = 5.0  # pseudo count of the season score level
    level_min_w: float = 1.0 / 3000.0  # floor of the season level update weight
    var_prior_n: float = 30.0  # pseudo count of the season score variance
    # ---- Rank-weighted alliance aggregation
    agg_k: float = 320.0  # ridge pseudo count of the per-season rank weights
    # ---- Cross-event (per-event PCG) ratings
    pcg_reg: float = 16.0  # ridge regularization (match count units)
    pcg_carry: float = 0.50  # weight of the cross-event rating in season-end carryover
    pcg_ev_carry: float = 0.40  # weight of the cross-event rating at a new event
    pcg_po_w: float = 0.5  # weight of 3v3 playoff matches in the normal equations
    # ---- Win probability
    shape_kn: float = 2000.0  # pseudo count of the normal prior shape
    shape_kp: float = 2000.0  # pseudo count of the pooled past-season shape
    elo_k: float = 0.03  # win-rating step per team (logit units)
    stack_pv: float = 0.1  # prior variance of the stacking weights
    stack_q: float = 3e-6  # per-match random-walk variance of the stacking weights
    stack_lvl_s0_qm: float = 3.0  # saturation scale of the score level in quals
    stack_lvl_s0_po: float = 1.5  # saturation scale of the score level in playoffs
    stack_agg_shrink: float = 0.25  # season-start shrinkage of the rank weights
    stack_po_pv: float = 0.02  # prior variance of the playoff stacker features
    dq_k: float = 50.0  # pseudo count (matches) of the team DQ-rate shrinkage
    dq_r0: float = 0.02  # prior team DQ rate
    # ---- Score residual shape (Gaussian mixtures)
    gmm_k: int = 5  # mixture components
    gmm_kn: float = 500.0  # pseudo count of the normal prior
    gmm_kp: float = 500.0  # pseudo count of the pooled past seasons
    gmm_sdscale: float = 1.02  # read-time component sd multiplier
    gmm_cond_kg: float = 2000.0  # shrinkage of a bucket shape toward the global shape
    gmm_cond_guard: int = 500  # matches per season that forecast with the global shape
    # ---- Score mean and width calibration
    score_cal_ka: float = 500.0  # ridge pseudo count of the intercept
    score_cal_kc: float = 500.0  # ridge pseudo count of the slope
    score_cal_decay: float = 0.999  # per-alliance forgetting factor
    foul_k: float = 10.0  # pseudo count (matches) of the team foul-rate shrinkage
    prog_k: float = 20.0  # pseudo count (alliance scores) of the shrinkage per bin
    sat_k: float = 300.0  # ridge pseudo count of the score saturation learner
    sat_huber: float = 0.65  # Huber threshold (sigma units) of the saturation learner
    sat_pool_decay: float = 0.85  # season-to-season decay of the saturation sums
    var_cal_k: float = 250.0  # ridge pseudo count of the variance calibration
    var_cal_decay: float = 0.999  # per-alliance forgetting factor
    var_cal_floor: float = 0.25  # lower bound of the variance multiplier
    # ---- Score structure (rulebook score components)
    struct_eta: float = 0.5  # learning rate of the mixture weights
    struct_alpha: float = 1e-3  # fixed-share rate of the mixture weights per match
    struct_lam: float = 0.25  # shrinkage of the mixture weights at a season start
    # ---- Playoff alliance synergy
    po_syn_k: float = 2.0  # pseudo count (playoff matches) of the residual shrinkage
    po_syn_s: float = 0.25  # residual weight on the expected score (sigma units)
    po_syn_d: float = 0.25  # residual weight on the standardized win margin
    # ---- Ranking points
    rp_prior_var: float = 4.0  # prior variance of each bonus RP logistic weight
    rp_q: float = 1e-4  # per-match random-walk variance of the bonus RP intercept
    rb_q_frac: float = 0.02  # per-match process variance of team sum channels
    rb_prior_share: float = 0.5  # prior share of channel variance explained by teams
    rb_z_prior: float = 0.70  # pre-season team skill weight in the channel cold start
    rb_decay: float = 0.95  # per-observation decay of team counts
    rb_prior_n: float = 3.0  # pseudo count of the season mix in team channels
    rb_cal_pv: float = 0.5  # prior variance of the rule calibration weights
    rb_cal_q: float = 1e-5  # per-match random-walk variance of the calibration weights
    rb_award_a: float = 0.5  # Beta prior of the award and deny rates
    rb_award_b: float = 20.0
    rp_rho_prior: float = 0.3  # prior mean of the bonus/outcome copula correlation
    rp_rho_sd: float = 0.2  # prior sd of the copula correlation


DEFAULT_CONFIG = HKFConfig()
