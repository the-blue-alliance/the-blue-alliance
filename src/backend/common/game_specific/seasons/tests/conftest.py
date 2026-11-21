import json
import os
from typing import Any, Dict, List, Optional

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.game_specific.base import SeasonGameConfig, TCriteria
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


# Insight keys derived only from alliance scores, never from a score breakdown.
SCORE_STATS = frozenset(
    {
        "average_win_score",
        "average_winning_score",
        "average_win_margin",
        "average_score",
        "high_score",
    }
)


def _all_zero(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_all_zero(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_zero(v) for v in value)
    if isinstance(value, str):
        return value == ""
    return value == 0


def _win_score(insights: Dict[str, Any]) -> float:
    if "average_winning_score" in insights:
        return insights["average_winning_score"]
    return insights["average_win_score"]


def assert_score_stats_without_breakdowns(
    config: SeasonGameConfig[Any], event_key: str
) -> None:
    """An event with no breakdowns gets score stats and zeroed breakdown stats."""
    matches = [
        build_match(event_key, "qm", 1, 30, 10, None),
        build_match(event_key, "qm", 2, 20, 40, {}),
        build_match(event_key, "qm", 3, -1, -1, None),
    ]
    insights = none_throws(config.calculate_event_insights(matches))
    qual = none_throws(insights["qual"])
    assert _win_score(qual) == 35
    assert qual["average_win_margin"] == 20
    assert qual["average_score"] == 25
    assert list(qual["high_score"]) == [40, matches[1].key_name, matches[1].short_name]
    assert _all_zero({k: v for k, v in qual.items() if k not in SCORE_STATS})
    assert insights["playoff"] is None


def assert_partial_breakdowns_split_counters(
    config: SeasonGameConfig[Any], matches: List[Match]
) -> None:
    """Score stats count every played match; breakdown stats only those with one."""
    first = matches[0]
    level = first.comp_level
    extras = [
        build_match(first.event_key_name, level, 901, 999, 0, None, 99),
        build_match(first.event_key_name, level, 902, 5, 7, {}, 99),
    ]
    base = none_throws(config.calculate_event_insights(matches))
    mixed = none_throws(config.calculate_event_insights(matches + extras))
    if level == CompLevel.QM:
        base_stats, stats = none_throws(base["qual"]), none_throws(mixed["qual"])
        assert mixed["playoff"] == base["playoff"]
    else:
        base_stats, stats = none_throws(base["playoff"]), none_throws(mixed["playoff"])
        assert mixed["qual"] == base["qual"]

    played = [
        m
        for m in matches + extras
        if (m.comp_level == CompLevel.QM) == (level == CompLevel.QM)
        and m.has_been_played
    ]
    reds = [m.alliances[AllianceColor.RED]["score"] for m in played]
    blues = [m.alliances[AllianceColor.BLUE]["score"] for m in played]
    wins = [max(r, b) for r, b in zip(reds, blues)]
    margins = [abs(r - b) for r, b in zip(reds, blues)]
    assert _win_score(stats) == sum(wins) / len(played)
    assert stats["average_win_margin"] == sum(margins) / len(played)
    assert stats["average_score"] == (sum(reds) + sum(blues)) / (2 * len(played))
    assert list(stats["high_score"]) == [999, extras[0].key_name, extras[0].short_name]

    for key, value in stats.items():
        if key not in SCORE_STATS:
            assert value == base_stats[key], key
