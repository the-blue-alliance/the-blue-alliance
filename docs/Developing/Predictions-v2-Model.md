## Predictions v2 model

The predictions v2 model (HKF, a hierarchical Kalman filter) forecasts FRC matches. For every match it gives:

* the probability that the red alliance wins (a tie counts as half a win),
* a distribution over each alliance's score, including penalty points,
* in qualification matches, each alliance's expected and median ranking points and the probability of each bonus ranking point.

The code is in `src/backend/common/helpers/predictions_v2/model/`. The pipeline that runs it is described in [[Predictions-v2]].

### Interface

The model is an online learner over a stream of matches in play order (see [Data](#data)).

| Call | What it does |
| :--- | :--- |
| `start_season(year)` | Rolls the finished season into the cross-season priors (see [Seasons](#seasons)) and resets the per-season learners. |
| `predict_match(context)` | Forecasts one match from the current state. It never changes state. |
| `update(context, outcome)` | Learns from one played match. |

A `MatchContext` (`types.py`) holds what is known before a match: the event key and type, the competition level and both alliances' team keys. A `MatchOutcome` holds the result: both scores, the win label, both score breakdowns, the bonus ranking points earned and the disqualified teams. The win label is 1 for a red win, 0 for a blue win and 0.5 for a tie. A playoff match decided by a tiebreaker counts as a win for the alliance that advanced.

Every learner trains on the same pre-match quantities that `predict_match` used: `update` computes all of them before it changes any state.

### Team strength

Each team has a two-dimensional latent strength per season, in units of the season's alliance-score standard deviation σ:

* `s`: the team's contribution to the shared alliance score (game pieces, alliance bonuses).
* `u`: the points the rulebook awards to that robot alone, for example auto mobility or the endgame climb. The score breakdown records them per driver station, and station N is the Nth team of the alliance. `rulebook._ROBOT_POINTS` maps the breakdown fields to points for 2016 to 2026.

**Observations.** Each alliance gives one shared-score observation (total − fouls received − robot points) and one robot-points observation per station. Without a breakdown, or in a season without a robot-points table, the filter observes the total score only. Fouls depend on the opponent, so they enter the forecast as a season mean and a noise term.

**Within an event,** a Kalman filter keeps a joint Gaussian over the `(s, u)` of every team that has played at the event, with the full covariance. A match updates it as follows:

* An alliance's expected shared score is a rank-weighted sum of its teams' `s`. The alliance score is convex in team strength, so the strongest robot counts more and the weakest less. The per-season rank weights are fit by ridge regression (`agg_k` = 320) on within-match differences.
* An opponent interaction γ, learned per season, subtracts a share of the opponents' strength.
* The red and blue shared-score noises are correlated (0.05).
* A Huber rule widens the noise of an innovation beyond 2.2 standard deviations, so one outlier match moves the state less.
* Each match adds a small process noise (0.3% of the prior covariance) to the teams that played.
* The season score level, the robot-points level, the noise variances and the team spreads are learned online, shrunk toward priors with a pseudo count of 1,000 alliance scores.

**Between events,** each team keeps only its marginal state. Entering a new event, its mean drifts up by 0.17σ and its covariance grows by 5% of the prior covariance.

**Cross-event ratings.** Each event keeps the normal equations of a ridge regression (`pcg_reg` = 16) of the alliance scores of its 3-team alliances on their teams. After every match the model solves the event's active teams by conjugate gradient, holding the ratings of their partners at earlier events fixed. Teams are solved in sorted key order, so the result does not depend on Python's string hash seed. The rating is used in three places:

* as a feature of the win probability;
* when a team enters a new event, 40% of the gap between its rating and its filter strength is added to its mean;
* at the end of the season, 50% of that gap is blended into the strength that carries over.

### Win probability

1. The filter gives the mean `d` and variance `v` of the standardized red − blue margin.
2. An empirical, symmetric CDF of standardized margin residuals maps `d / √v` to a probability. It mixes a normal prior (weight 2,000), the pooled residuals of past seasons (weight 2,000) and this season's residuals, on 0.05σ bins.
3. An online Bayesian logistic regression (the stacker) combines that probability's logit with 11 more red − blue features:
   * a slow win rating, an Elo-like rating that steps 0.03 per match and does not decay across seasons;
   * the difference of the strongest and of the weakest team's total strength;
   * the number of earlier events played this season;
   * the predictive variance;
   * the cross-event rating residual;
   * the logit times the expected score level above the season mean, saturated above 0 at 3.0 in qualification matches and 1.5 in playoffs (the same gap is less decisive in a high-scoring match);
   * shrunk team disqualification rates (qualification matches only);
   * three playoff-only terms (the weakest-team gap, the robot-points gap, the cross-event residual).

The stacker's weights start at 1 on the logit and 0 elsewhere and drift slowly. Every feature changes sign under a red/blue swap, and the stacker has no intercept, so swapping the alliances gives exactly `1 − p`.

### Score distribution

The score forecast is a probability for every integer score of 0 and above. The API reports its mean, standard deviation and 10th, 50th and 90th percentiles.

**Mean.** The filter forecast plus:

* an event-progress offset, because scores rise during an event (12 bins of matches played, learned per season and pooled across seasons);
* an online ridge recalibration of the mean on the forecast level;
* a foul-transfer term, from each opposing team's shrunk rate of foul points given;
* the 2016 and 2017 playoff threshold bonuses, which score points in playoffs instead of ranking points;
* a within-event residual of a fixed playoff alliance;
* a Huber-clipped ridge calibration for playoff progression, opponent defense and the sub-additivity of two strong teams on one alliance.

**Spread.** The filter's predictive standard deviation, rescaled to the season's observed score variance, times an online calibration `√(c0 + c1·x)`. Here `x` is the forecast level, because scores vary more when more is scored. In 2016 and 2017 playoffs it adds the variance of the threshold bonuses.

**Shape.** The base distribution is `mean + sd · T`, placed on the integers ≥ 0. `T` is a learned residual shape (`gmm_shape.py`): a 5-component Gaussian mixture fit by weighted EM to the standardized residuals of past matches. It mixes a normal prior (weight 500), the pooled past seasons (weight 500) and this season's residuals. There is one mixture per bucket (qualification or playoff × three forecast levels), shrunk toward the global mixture with weight 2,000. During the first 500 matches of a season the forecast uses the global mixture.

**Rulebook structure.** Many games score in fixed steps, for example 2017's 40-point rotors and 50-point climbs. `rulebook.SCORE_COMPONENTS` lists, per season, the breakdown fields that add up to the alliance score and each field's point step (the gcd of the point values the field can hold), taken from the game manual. A component model (`structure.py`) learns, per component, the distribution of counts given team strength. Their convolution is a stepped distribution. The forecast mixes the base distribution with "base × the stepped fine structure", and the mixture weight is learned online across seasons. The result is shifted so its mean stays the base mean. The structure changes only the distribution's shape: win probability, score mean and ranking points do not depend on it. A season without a table, or a field missing from the breakdown, falls back to the base distribution.

### Ranking points

* **Win and tie values:** 2 and 1 before 2025, 3 and 1 from 2025 (`rp_pmf.rp_values`).
* **Bonus ranking points** (`bonus.py`) are modeled from the rulebook.
  * Each season defines the quantities its rules use (a game-piece count, endgame points, per-robot climb states, coopertition). Team-level channels learn them online: a Gaussian sum per team, a categorical per-robot state, or a per-team yes/no rate.
  * The rule combines the channel distributions with the threshold of the event's tier: regional or district event, district championship, or championship.
  * An online logistic calibration maps the rule probability to the probability that the flag is set. Learned rates of flags set without the rule (foul awards) and of flags missing although the rule was met correct it.
  * Before the channels have data, an online logistic model on the filter's strength features is the fallback (`rp.py`).
* **Expected ranking points** = win value × P(win) + tie value × P(tie) + Σ bonus probabilities.
* **Median ranking points** come from a joint distribution (`rp_pmf.py`): a Gaussian copula on the match outcome links win, tie and each bonus. A strong alliance tends to win and to reach thresholds in the same match. The correlation of each bonus with the outcome is learned per season, and the tie probability per season. Every marginal stays exact.

### Seasons

`start_season` rolls the finished season over:

* **Team strength.** It blends the cross-event rating in, subtracts the season's mean drift, and records each team's season-end total.
* **The new season's prior mean** is 0.78 per season of gap times last season's total, blended with up to three older seasons (weight 0.35). The prior covariance keeps 0.75 per season of gap of the explained variance.
* **Rookies** start 0.5 prior standard deviations below the mean.
* **Pooled into cross-season priors:** the score level and spread, the rank weights, the progress offsets, the playoff and saturation calibrations, the margin shape and the score shapes.
* **Shrinks the stacker's rank weights** toward 0 and the structure mixture weights toward uniform.
* **Resets** the event states, the bonus-RP models and the joint-RP correlations.

The within-event state of an event is only read by that event's matches. The pipeline drops it a week after the event ends; this doesn't change any prediction.

### Learned and fixed

| | |
| :--- | :--- |
| Learned online, per season | Team states, event states, cross-event ratings, score level and noise, rank weights, opponent interaction, calibrations, progress offsets, score shapes, component models, bonus channels and calibrations, joint-RP correlations, DQ and foul rates |
| Carried across seasons | Team totals and history, win ratings, stacker weights, margin and score shape pools, pooled calibrations, structure mixture weights, tie rate |
| Fixed in code | `HKFConfig` (the model's hyperparameters), numerical settings kept as module constants (grid widths, supports, bin counts, EM schedules), the rulebook tables in `rulebook.py` and `bonus.py` |

Hyperparameters are never stored with the model state. The state header records a fingerprint of `HKFConfig`, the rulebook tables and `MODEL_VERSION`, and a state with another fingerprint is not loaded (`state.py`).

### Guarantees and tests

| Guarantee | Test |
| :--- | :--- |
| No lookahead: `update` computes every pre-match quantity before it changes state. | Golden stream |
| `predict_match` never changes state, including the forecast of an offseason match. | `predictor_test.py` |
| Replay is deterministic and does not depend on the hash seed. | Golden stream: 2,773 matches, 2016–2025 |
| Saving and loading the state at any point does not change any later prediction. | `predictor_test.py` |
| Dropping a finished event's state does not change any later prediction. | `predictor_test.py` |
| Each season's score components add up to the score on at least 98% of real breakdowns, with no value off its step. | `rulebook_test.py` |

The golden stream (`helpers/tests/predictions_v2/model/golden.py`) pins every prediction of 2,773 PNW district matches. Its expected values were first generated by an independent implementation of the same model, and this implementation matches them exactly. After an intended change, regenerate them as described in `golden.py`.

### Data

The model learns from TBA's own match data, replayed season by season from 2002 in event-block order:
* matches inside an event in bracket order;
* concurrent events interleaved by match time;
* each season one contiguous block.

**Training stream.** Every played match of an event of type 0–6 (regional, district, district championship and its divisions, championship divisions and finals, Festival of Champions) is predicted, then learned. Practice matches and unplayed matches are never in the stream. Remote events are excluded. Offseason and preseason matches are predicted but never learned from: their teams, rules and stakes differ. Each prediction is made before its match's result is known.

**Splits.** The hyperparameters, the model's components and the rulebook tables were chosen with these holdout rules:

| Split | Seasons | Use |
| :--- | :--- | :--- |
| Development | 2016–2024, except 2021 | Every design choice and hyperparameter was selected here (about 116,000 matches). The full stream from 2002 is replayed, and only these seasons are scored. 2002–2015 serve as warmup; most of them have no score breakdowns. |
| Validation | 2025 | Held out from development. Each frozen version of the model was confirmed on it once, with the run approved in advance and recorded. |
| Test | 2026 | Sealed. The model was not run on it during development. |

* **2025 was used lightly, not left untouched.**
  * It was scored six times over the model's development, once per frozen version, each after that version's development on 2016–2024 was finished.
  * The final confirmation scored the chosen configuration together with three nearby variants. One choice was made on that run: the bucket shrinkage, 2,000 against 600, was decided on score NLL, and the two have identical win and ranking-point metrics.
  * Treat 2025 as a validation season, not an untouched test season.
* **2026 is the clean test season.**
  * The model was never run on it before the backtest below.
  * Four recorded reads of 2026 happened during development, all with simple reference baselines or an external predictor, never with this model. They wrote no per-match records and reported only aggregate numbers.
* **Scoring rules:**
  * ties count as 0.5;
  * accuracy counts decided matches only;
  * score MAE is per alliance, on the distribution's mean;
  * bonus RP Brier is per alliance and key, in qualification matches with a recorded flag.

**Results.**

| Split | Matches | Win Brier | Log loss | Accuracy | Score MAE | v1 Brier | v1 accuracy |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Development (2016–2024) | ~116,000 | 0.1608 | 0.4912 | 0.754 | 23.65 | | |
| Validation (2025) | 17,846 | 0.1386 | 0.4283 | 0.796 | 17.82 | 0.1760 | 0.729 |
| Test (2026) | 18,372 | 0.1298 | 0.4046 | 0.813 | 47.47 | 0.1716 | 0.751 |

Notes on the table:
* **How it was measured.** The 2025 and 2026 rows come from `ops/predictions_v2_backtest.py`: the full stream from 2002, with the v1 predictor scored on the same matches. The development row comes from the model's development runs.
* **Score MAE across seasons.** Scores are on each game's scale, so score MAE is not comparable across seasons; 2026 games score several hundred points.
* **Bonus RP Brier:** 0.1371 in 2025 and 0.0568 in 2026.

**Holdout rules from here on:**
* **Develop changes on 2016–2024.** Confirm a frozen change once on 2025 and record the result in the change's PR.
* **Report 2026, never tune on it.** A change tuned on 2026 would make the test numbers above meaningless.
* **After the 2027 season,** 2026 joins validation and 2027 becomes the test season.

### Changing the model

* **Bump `MODEL_VERSION`.** Any change to the model code, to `HKFConfig` or to the rulebook tables changes predictions and must bump it in `predictor.py`. The pipeline then rebuilds every season from 2002 (see [[Predictions-v2]]).
* **Regenerate the golden stream** and review its diff in the PR.
* **Rerun the backtest** on the validation season and report the change in every metric.
* **Add each new game's tables at kickoff.** The checklist is in [[Predictions-v2]].
