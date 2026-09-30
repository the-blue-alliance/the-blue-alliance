#!/usr/bin/env python3
"""Historical backfill and seeding script for SOTA FRC match predictions.

Streams past season matches in canonical interleaved order, calculates
hierarchical Kalman filter (hkf_ev_pcg) predictions, and populates
EventPredictionsV2, SeasonPredictionState, and checkpoints in Datastore/GCS.
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Set

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
)
from backend.common.models.match import Match
from backend.common.models.prediction_state import (
    SeasonPredictionCheckpoint,
    SeasonPredictionState,
)
from backend.tasks_cpu.handlers.predictions import (
    _extract_team_rating,
    _format_ranking_points,
    _format_score_distribution,
    _is_played,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def seed_season(season: int) -> None:
    logging.info(f"Starting SOTA prediction seeding for season {season}...")

    matches = Match.query(Match.year == season).fetch()
    played_matches = [m for m in matches if _is_played(m)]
    if not played_matches:
        logging.warning(f"No played matches found for season {season}. Skipping.")
        return

    events = Event.query(Event.year == season).fetch()
    event_lookup: Dict[str, Event] = {ev.key_name: ev for ev in events}

    logging.info(
        f"Sorting {len(played_matches)} played matches across {len(events)} events..."
    )
    sorted_matches = sort_replay_stream(
        played_matches, events=event_lookup, mode="interleaved"
    )

    pred = HKFEventPCGPredictor()
    pred.start_season(season)

    logging.info(
        f"Streaming {len(sorted_matches)} matches through HKFEventPCGPredictor..."
    )
    for idx, m in enumerate(sorted_matches, start=1):
        event = event_lookup.get(m.event_key_name)
        if event is None:
            continue
        outcome = to_match_outcome(m, event)
        if outcome is not None:
            pred.update(outcome)

        if idx % 100 == 0 or idx == len(sorted_matches):
            logging.info(f"Processed {idx}/{len(sorted_matches)} matches...")
            try:
                cp_blob = pred.dump_state()
                cp_path = f"predictions/{season}/checkpoint_{idx}.bin.gz"
                storage.write(cp_path, cp_blob, content_type="application/octet-stream")
                cp_entity = SeasonPredictionCheckpoint(
                    id=f"{season}_{idx}",
                    season=season,
                    match_step=idx,
                    last_match_key=m.key_name,
                    timestamp=int(time.time()),
                    gcs_blob_path=cp_path,
                )
                cp_entity.put()
            except Exception as e:
                logging.warning(f"Could not persist checkpoint {idx}: {e}")

    # Prune concluded events
    active_keys = [ev.key_name for ev in events if not getattr(ev, "concluded", False)]
    pred.prune_dead_state(active_keys)

    # Save active state to GCS and metadata
    active_path = f"predictions/{season}/state_active.bin.gz"
    active_blob = pred.dump_state()
    try:
        storage.write(active_path, active_blob, content_type="application/octet-stream")
        state = SeasonPredictionState.get_by_id(str(season)) or SeasonPredictionState(
            id=str(season), season=season
        )
        state.match_count = len(pred.processed_match_keys)
        state.last_match_key = sorted_matches[-1].key_name if sorted_matches else None
        state.gcs_blob_path = active_path
        state.processed_match_keys_json = list(pred.processed_match_keys)
        state.put()
    except Exception as e:
        logging.warning(f"Could not persist active season state: {e}")

    # Generate EventPredictionsV2 for each event
    logging.info(f"Generating EventPredictionsV2 for {len(events)} events...")
    matches_by_event: Dict[str, List[Match]] = {}
    for m in matches:
        matches_by_event.setdefault(m.event_key_name, []).append(m)

    for ev in events:
        ev_matches = matches_by_event.get(ev.key_name, [])
        if not ev_matches:
            continue

        match_predictions: Dict[str, MatchPredictionV2] = {}
        participating_teams: Set[str] = set()

        for m in ev_matches:
            for t in m.team_key_names:
                participating_teams.add(t)

            ctx = to_match_context(m, ev)
            p = pred.predict_match(ctx)

            red_win = p.red_win_prob
            winning_alliance = (
                AllianceColor.RED
                if red_win > 0.5
                else (AllianceColor.BLUE if red_win < 0.5 else None)
            )
            win_prob = red_win if red_win >= 0.5 else (1.0 - red_win)

            rp_dict = None
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

        team_ratings = {t: _extract_team_rating(pred, t) for t in participating_teams}

        last_played = [m for m in ev_matches if _is_played(m)]
        as_of_match = last_played[-1].key_name if last_played else None

        payload: EventPredictionsV2Payload = {
            "model_version": "hkf_ev_pcg_v1.0",
            "as_of_match": as_of_match,
            "last_updated": datetime.now(timezone.utc).isoformat(),  # pyre-ignore[16]
            "matches": match_predictions,
            "team_ratings": team_ratings,
        }

        event_preds = EventPredictionsV2.get_by_id(ev.key_name) or EventPredictionsV2(
            id=ev.key_name
        )
        event_preds.predictions = payload
        event_preds.as_of_match = as_of_match
        EventPredictionsV2Manipulator.createOrUpdate(event_preds)

    logging.info(f"Completed seeding for season {season}!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SOTA predictions")
    parser.add_argument("--season", type=int, help="Single season to seed (e.g. 2024)")
    parser.add_argument(
        "--start-season",
        type=int,
        default=2016,
        help="First season to seed (default: 2016)",
    )
    parser.add_argument(
        "--end-season",
        type=int,
        default=2026,
        help="Last season to seed (default: 2026)",
    )
    args = parser.parse_args()

    if args.season:
        seed_season(args.season)
    else:
        for s in range(args.start_season, args.end_season + 1):
            seed_season(s)


if __name__ == "__main__":
    main()
