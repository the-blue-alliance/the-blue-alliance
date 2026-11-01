## Predictions v2

Predictions v2 forecasts every match with the HKF model (`src/backend/common/helpers/predictions_v2/`): the red alliance's win probability, each alliance's score distribution, and qualification ranking points. It is served at `GET /api/v3/event/{event_key}/predictions_v2`.

How the model works, and the data it was developed, validated and tested on, are in [[Predictions-v2-Model]]. This page covers the pipeline that runs it.

The `predictions_v2_config` sitevar is the kill switch. While `enabled` is false (the default), every predictions_v2 task does nothing.

### How it works

* **Stream.** Each season is replayed match by match in event-block order (bracket order inside an event, concurrent events interleaved by match time). Matches of event types 0–6 (regional through FOC) train the model. Offseason and preseason matches are predicted but never learned from. Remote and unlabeled events, practice matches and unplayed matches are not in the stream.
* **Seasons carry over.** A season starts from the previous season's state (back to 2002), and the model rolls over at the season's first training match.
* **State.** `SeasonPredictionState` points at a season's model state, match log and checkpoints in Cloud Storage (`predictions_v2/<season>/`). The log holds every applied match with the prediction made before its result was known. Every blob is written to the slot the entity does not point at, so a failed write leaves the previous state intact.
* **Updates.** Every 2 minutes the cron (`/backend-tasks-b2/enqueue/math/predictions_v2/advance`, on `py3-tasks-cpu-enqueue`) compares each active event's matches with the digest stored on its `EventPredictionsV2`. Only when something changed does it enqueue an advance task on `py3-tasks-cpu`, on the serial `predictions-v2` queue (one writer). The task appends new results to the log, also when they arrive late, and rewrites the predictions of every changed event: the logged pre-match prediction of each played match and a forecast of each unplayed one.
* **Corrections.** When the result of a match that is already in the log changes (score, breakdown, teams, DQs), or the match is deleted or reset to unplayed, the season rewinds: the newest checkpoint at or before that log entry is loaded and the rest of the log is replayed with the current match data. Every later prediction is recomputed. A nightly reconcile (04:00 PT) checks every event of the current season, so corrections to finished events are caught too. A correction to last season after the new season has started does not carry into the new season until the next rebuild.

### Runbook

All routes are admin-only task routes.

* **First deploy (backfill).** Enable the sitevar, then open `/backend-tasks-b2/enqueue/math/predictions_v2/rebuild/2002?chain=1`. Each season replays in its own task and then enqueues the next season, through the max season. Expect a few minutes per modern season.
* **Model change.** A change to the model code, its configuration or its rulebook tables must bump `MODEL_VERSION` in `model/predictor.py`. A stored state of another version is never loaded: the next advance enqueues a chained rebuild from 2002 (once per version) and does nothing until the current season is rebuilt. A rebuild holds the queue, so deploy model changes outside event hours.
* **Rebuild one season.** `/backend-tasks-b2/enqueue/math/predictions_v2/rebuild/<season>` (add `?chain=1` to rebuild every later season too, which a season with changed results needs for the carryover to reach later seasons).
* **Backtest.** `uv run python ops/predictions_v2_backtest.py --data <dir> --score 2025,2026 --v1` replays APIv3 JSON offline and compares v2 with v1 on the same matches.

### Kickoff checklist

The model reads each game's scoring rules from tables. Without a new season's entries it still runs, but its score distributions and ranking point forecasts are worse, and nothing fails loudly. At kickoff, from the game manual:

1. `model/rulebook.py`, `_ROBOT_POINTS`: the points one robot earns alone (mobility, endgame) and the per-station breakdown fields that record them.
2. `model/rulebook.py`, `SCORE_COMPONENTS`: the breakdown fields that add up to the alliance score, with each field's point step (the gcd of the values it can hold) and whether it only scores in playoffs. `rulebook_test.py` checks that they add up on the season's match fixture, so add a fixture event once matches are played.
3. `model/bonus.py`: the bonus RP flag fields in `BONUS_RP_FIELDS`, the rules in `rule_met` and `rule_probs`, their channels, and the thresholds per event tier in `TIER_THRESHOLDS`. Add the season to `SUPPORTED_BONUS_SEASONS`.
4. `model/rp_pmf.py`, `rp_values`: the win and tie RP values, if they change.
5. Bump `MODEL_VERSION` and rebuild the new season.
