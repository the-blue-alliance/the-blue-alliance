import logging
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from flask import abort, Blueprint, make_response
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common import storage
from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.sota_prediction import (
    HKFEventPCGPredictor,
    sort_replay_stream,
    to_match_context,
    to_match_outcome,
)
from backend.common.manipulators.event_predictions_v2_manipulator import (
    EventPredictionsV2Manipulator,
)
from backend.common.models.event import Event
from backend.common.models.event_predictions_v2 import (
    EventPredictionsV2,
    EventPredictionsV2Payload,
    MatchPredictionV2,
    RankingPointsPredictionPayload,
    ScoreDistribution,
    TeamRatingV2,
)
from backend.common.models.keys import EventKey, MatchKey, TeamKey
from backend.common.models.match import Match
from backend.common.models.prediction_state import (
    SeasonPredictionCheckpoint,
    SeasonPredictionState,
)

blueprint = Blueprint("predictions", __name__)

_WARM_PREDICTORS: Dict[int, HKFEventPCGPredictor] = {}


def _get_or_load_predictor(season: int) -> HKFEventPCGPredictor:
    """Retrieve warm predictor from memory, fallback to GCS checkpoint, or initialize fresh."""
    if season in _WARM_PREDICTORS:
        return _WARM_PREDICTORS[season]

    pred = HKFEventPCGPredictor()
    state = SeasonPredictionState.get_by_id(str(season))
    if state and state.gcs_blob_path:
        blob_bytes = storage.read(state.gcs_blob_path)
        if blob_bytes and isinstance(blob_bytes, (bytes, bytearray)):
            try:
                pred.load_state(bytes(blob_bytes))
                _WARM_PREDICTORS[season] = pred
                return pred
            except Exception:
                logging.exception(
                    f"Failed to load state blob from {state.gcs_blob_path} for season {season}"
                )

    pred.start_season(season)
    _WARM_PREDICTORS[season] = pred
    return pred


def _is_played(match: Match) -> bool:
    """Check if match has finalized scores."""
    alliances = match.alliances
    if not isinstance(alliances, dict):
        return False
    red = alliances.get(AllianceColor.RED) or alliances.get("red")  # pyre-ignore[6]
    blue = alliances.get(AllianceColor.BLUE) or alliances.get("blue")  # pyre-ignore[6]
    return (
        isinstance(red, dict)
        and isinstance(blue, dict)
        and int(red.get("score", -1)) >= 0
        and int(blue.get("score", -1)) >= 0
    )


def _format_score_distribution(score_pred: Any) -> ScoreDistribution:
    """Convert ScorePrediction into APIv3 ScoreDistribution schema."""
    mean_val = round(score_pred.expected_value(), 2)
    pmf_map: Dict[int, float] = {}
    sd_val = 0.0
    if score_pred.pmf is not None:
        for k, p in score_pred.pmf.items():
            pmf_map[int(k)] = round(float(p), 4)
        var = sum((k - mean_val) ** 2 * p for k, p in score_pred.pmf.items())
        sd_val = round(math.sqrt(max(0.0, var)), 2)
    return {
        "mean": mean_val,
        "sd": sd_val,
        "pmf": pmf_map,
    }


def _format_ranking_points(rp_pred: Any) -> RankingPointsPredictionPayload:
    """Convert RankingPointsPrediction into APIv3 RankingPointsPredictionPayload."""
    exp_rp = round(rp_pred.expected_rp or 0.0, 3) if rp_pred else 0.0
    med_rp = int(rp_pred.median_rp or 0) if rp_pred else 0
    bonuses: Dict[str, float] = {}
    if rp_pred and rp_pred.bonus_rp_probs:
        for k, v in rp_pred.bonus_rp_probs.items():
            bonuses[k] = round(float(v), 4)
    return {
        "expected_rp": exp_rp,
        "median_rp": med_rp,
        "rp_pmf": {},
        "bonus_probabilities": bonuses,
    }


def _extract_team_rating(pred: HKFEventPCGPredictor, team_key: str) -> TeamRatingV2:
    """Extract SOTA rating components (s, u, win_rating, pcg_rating) for a team."""
    st = pred.teams.get(team_key)
    s_val = float(st[0][0]) if st is not None else 0.0
    u_val = float(st[0][1]) if st is not None else 0.0

    wr_entry = pred.wr.get(team_key)
    win_val = float(wr_entry[0]) if wr_entry is not None else 0.0

    pcg_val = 0.0
    pcg_z = getattr(pred, "pcg_z", None)
    ev_pcg = getattr(pred, "ev_pcg", None)
    if isinstance(pcg_z, dict) and team_key in pcg_z:
        pcg_val = float(pcg_z[team_key])
    elif isinstance(ev_pcg, dict):
        for ev_state in ev_pcg.values():
            if len(ev_state) > 2 and team_key in ev_state[2]:
                pcg_val = float(ev_state[2][team_key])
                break

    return {
        "shared_strength": round(s_val, 2),
        "robot_strength": round(u_val, 2),
        "win_rating": round(win_val, 2),
        "pcg_rating": round(pcg_val, 2),
    }


@blueprint.route("/tasks/math/do/season_predictions_advance/<int:season>")
def season_predictions_advance(season: int) -> Response:
    """
    Monotonic Season Stream Worker.
    Processes played matches in canonical interleaved order and triggers projections.
    """
    matches = Match.query(Match.year == season).fetch()
    played_matches = [m for m in matches if _is_played(m)]
    if not played_matches:
        return make_response("No played matches found for season", 200)

    events = Event.query(Event.year == season).fetch()
    event_lookup: Dict[str, Event] = {ev.key_name: ev for ev in events}

    # Sort matches in canonical two-level event-block order
    sorted_matches = sort_replay_stream(
        played_matches, events=event_lookup, mode="interleaved"
    )

    pred = _get_or_load_predictor(season)
    processed_keys: Set[str] = set(pred.processed_match_keys)

    # Find unapplied matches
    unapplied_indices = [
        i for i, m in enumerate(sorted_matches) if m.key_name not in processed_keys
    ]
    if not unapplied_indices:
        return make_response("All played matches already processed", 200)

    first_unapplied_idx = unapplied_indices[0]

    # Check for chronological rewind need:
    # If any match after first_unapplied_idx was already processed, stream order was breached
    needs_rewind = any(
        m.key_name in processed_keys for m in sorted_matches[first_unapplied_idx:]
    )

    if needs_rewind:
        logging.warning(
            f"Chronological inversion detected at index {first_unapplied_idx}. Initiating rewind."
        )
        # Search for checkpoint before first_unapplied_idx
        checkpoints = (
            SeasonPredictionCheckpoint.query(
                SeasonPredictionCheckpoint.season == season,
                SeasonPredictionCheckpoint.match_step <= first_unapplied_idx,
            )
            .order(-SeasonPredictionCheckpoint.match_step)
            .fetch(1)
        )

        rewound = False
        if checkpoints and checkpoints[0].gcs_blob_path:
            blob = storage.read(checkpoints[0].gcs_blob_path)
            if blob and isinstance(blob, (bytes, bytearray)):
                try:
                    pred = HKFEventPCGPredictor()
                    pred.load_state(bytes(blob))
                    _WARM_PREDICTORS[season] = pred
                    rewound = True
                except Exception:
                    logging.exception(
                        f"Failed to load checkpoint {checkpoints[0].gcs_blob_path}"
                    )

        if not rewound:
            pred = HKFEventPCGPredictor()
            pred.start_season(season)
            _WARM_PREDICTORS[season] = pred

    # Process unapplied matches
    affected_events: Set[str] = set()
    for m in sorted_matches:
        if m.key_name in pred.processed_match_keys:
            continue

        event = event_lookup.get(m.event_key_name)
        if event is None:
            continue
        outcome = to_match_outcome(m, event)
        if outcome is not None:
            pred.update(outcome)
            affected_events.add(m.event_key_name)

        step = len(pred.processed_match_keys)
        if step > 0 and step % 100 == 0:
            # Checkpoint every 100 matches
            try:
                cp_blob = pred.dump_state()
                cp_path = f"predictions/{season}/checkpoint_{step}.bin.gz"
                storage.write(cp_path, cp_blob, content_type="application/octet-stream")
                cp_entity = SeasonPredictionCheckpoint(
                    id=f"{season}_{step}",
                    season=season,
                    match_step=step,
                    last_match_key=m.key_name,
                    timestamp=int(time.time()),
                    gcs_blob_path=cp_path,
                )
                cp_entity.put()
            except Exception:
                logging.exception(f"Failed to save checkpoint for step {step}")

    # Prune dead event state to bound active size (< 2.5 MB)
    active_event_keys = [
        ev.key_name for ev in events if not getattr(ev, "concluded", False)
    ]
    pred.prune_dead_state(active_event_keys)

    # Persist active state blob to GCS
    active_path = f"predictions/{season}/state_active.bin.gz"
    active_blob = pred.dump_state()
    storage.write(active_path, active_blob, content_type="application/octet-stream")

    # Update SeasonPredictionState metadata in Datastore
    state = SeasonPredictionState.get_by_id(str(season)) or SeasonPredictionState(
        id=str(season), season=season
    )
    state.match_count = len(pred.processed_match_keys)
    state.last_match_key = sorted_matches[-1].key_name if sorted_matches else None
    state.gcs_blob_path = active_path
    state.processed_match_keys_json = list(pred.processed_match_keys)
    state.put()

    # Enqueue projection workers for affected events
    for ev_key in affected_events:
        try:
            taskqueue.add(
                url=f"/tasks/math/do/event_predictions_project/{ev_key}",
                method="GET",
                target="py3-tasks-cpu",
                queue_name="event-predictions-project",
            )
        except Exception:
            logging.exception(f"Error enqueuing event_predictions_project for {ev_key}")

    return make_response(
        f"Advanced {len(sorted_matches)} matches for season {season}. Enqueued {len(affected_events)} event projections.",
        200,
    )


@blueprint.route("/tasks/math/do/event_predictions_project/<event_key>")
def event_predictions_project(event_key: EventKey) -> Response:
    """
    Event Projection Worker.
    Calculates match forecasts and team ratings for an event and stores EventPredictionsV2.
    """
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    season = event.year
    pred = _get_or_load_predictor(season)

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    if not matches:
        return make_response("No matches for event", 200)

    # Project forecasts for all matches
    match_predictions: Dict[MatchKey, MatchPredictionV2] = {}
    participating_teams: Set[str] = set()

    for m in matches:
        for t in m.team_key_names:
            participating_teams.add(t)

        ctx = to_match_context(m, event)
        p = pred.predict_match(ctx)

        red_win = p.red_win_prob
        winning_alliance: Optional[AllianceColor] = None
        if red_win > 0.5:
            winning_alliance = AllianceColor.RED
        elif red_win < 0.5:
            winning_alliance = AllianceColor.BLUE

        win_prob = red_win if red_win >= 0.5 else (1.0 - red_win)

        rp_dict: Optional[Dict[str, RankingPointsPredictionPayload]] = None
        if m.comp_level == "qm" and (p.red_rp or p.blue_rp):
            rp_dict = {
                "red": _format_ranking_points(p.red_rp),
                "blue": _format_ranking_points(p.blue_rp),
            }

        match_predictions[m.key_name] = {
            "match_key": m.key_name,
            "winning_alliance": winning_alliance,
            "win_probability": round(win_prob, 4),
            "red_win_prob": round(red_win, 4),
            "red": _format_score_distribution(p.red_score),
            "blue": _format_score_distribution(p.blue_score),
            "ranking_points": rp_dict,
        }

    # Extract team ratings for all participating teams
    team_ratings: Dict[TeamKey, TeamRatingV2] = {
        t: _extract_team_rating(pred, t) for t in participating_teams
    }

    last_played = [m for m in matches if _is_played(m)]
    as_of_match: Optional[str] = last_played[-1].key_name if last_played else None

    payload: EventPredictionsV2Payload = {
        "model_version": "hkf_ev_pcg_v1.0",
        "as_of_match": as_of_match,
        "last_updated": datetime.now(timezone.utc).isoformat(),  # pyre-ignore[16]
        "matches": match_predictions,
        "team_ratings": team_ratings,
    }

    event_preds = EventPredictionsV2.get_by_id(event_key) or EventPredictionsV2(
        id=event_key
    )
    event_preds.predictions = payload
    event_preds.as_of_match = as_of_match
    EventPredictionsV2Manipulator.createOrUpdate(event_preds)

    return make_response(
        f"Projected predictions for {len(matches)} matches at {event_key}.", 200
    )
