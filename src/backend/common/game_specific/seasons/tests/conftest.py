import json
import os
from typing import Any, Dict, List, Optional

from google.appengine.ext import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.game_specific.base import TCriteria
from backend.common.models.event import Event
from backend.common.models.match import Match

# Sentinel: dirname(_HELPERS_TESTS) == .../helpers/tests/ so that
# test_data_importer._get_path() resolves files from that directory.
HELPERS_TESTS = os.path.join(os.path.dirname(__file__), "../../../helpers/tests/x")


def tiebreak_winner(criteria: List[Optional[TCriteria]]) -> str:
    """Walk criteria list, return winning AllianceColor or empty string."""
    for c in criteria:
        if c is None:
            break
        if c[0] > c[1]:
            return AllianceColor.RED
        elif c[1] > c[0]:
            return AllianceColor.BLUE
    return ""


def put_event(event_key: str, event_type: EventType) -> Event:
    """Stores a minimal Event so that match.event.get() resolves."""
    event = Event(
        id=event_key,
        year=int(event_key[:4]),
        event_short=event_key[4:],
        event_type_enum=event_type,
    )
    event.put()
    return event


def build_match(
    event_key: str,
    comp_level: str,
    match_number: int,
    red_score: int,
    blue_score: int,
    score_breakdown: Optional[Dict[str, Any]],
    set_number: int = 1,
) -> Match:
    """
    Builds an unsaved Match for insight tests. A score of -1 marks the match
    as unplayed; a None score_breakdown models a match FIRST never
    published details for.
    """
    level = CompLevel(comp_level)
    return Match(
        id=Match.render_key_name(event_key, level, set_number, match_number),
        event=ndb.Key(Event, event_key),
        year=int(event_key[:4]),
        comp_level=level,
        set_number=set_number,
        match_number=match_number,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=json.dumps(
            {
                "red": {
                    "score": red_score,
                    "teams": ["frc1", "frc2", "frc3"],
                    "surrogates": [],
                    "dqs": [],
                },
                "blue": {
                    "score": blue_score,
                    "teams": ["frc4", "frc5", "frc6"],
                    "surrogates": [],
                    "dqs": [],
                },
            }
        ),
        score_breakdown_json=(
            None if score_breakdown is None else json.dumps(score_breakdown)
        ),
    )
