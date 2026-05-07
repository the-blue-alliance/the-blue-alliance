import json

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.helpers.insights_v2.streaks.win_streak import (
    LongestWinStreakV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.match import Match

# Red: frc1/frc2/frc3, Blue: frc4/frc5/frc6
_ALL_TEAMS = ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]


def _alliances_json(red_score: int, blue_score: int) -> str:
    return json.dumps(
        {
            "red": {"score": red_score, "teams": ["frc1", "frc2", "frc3"]},
            "blue": {"score": blue_score, "teams": ["frc4", "frc5", "frc6"]},
        }
    )


def _put_event(
    event_key: str, year: int, event_type: EventType = EventType.REGIONAL
) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
    ).put()


def _put_match(
    event_key: str,
    year: int,
    red_score: int,
    blue_score: int,
    match_number: int = 1,
) -> None:
    Match(
        id=f"{event_key}_qm{match_number}",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, event_key),
        year=year,
        match_number=match_number,
        set_number=1,
        team_key_names=_ALL_TEAMS,
        alliances_json=_alliances_json(red_score, blue_score),
    ).put()


def _calc() -> LongestWinStreakV2Calculator:
    return LongestWinStreakV2Calculator()


def test_consecutive_wins_build_streak(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    assert len(insights) == 1
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 3
    assert entries["frc1"]["start"] == "2024nyny"
    assert entries["frc1"]["end"] == "2024nyny"
    assert entries["frc1"]["is_active"] is True

    # Blue lost all 3 — no entry
    assert "frc4" not in entries


def test_loss_resets_streak(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=2)
    _put_match("2024nyny", 2024, red_score=5, blue_score=10, match_number=3)  # loss
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=4)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    # Best streak was 2 before the loss; the 1-win streak after does not exceed it
    assert entries["frc1"]["streak_length"] == 2
    assert entries["frc1"]["is_active"] is False


def test_streak_after_loss_becomes_best(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    _put_match("2024nyny", 2024, red_score=5, blue_score=10, match_number=2)  # loss
    for i in range(3, 8):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    # Post-loss streak of 5 is the best
    assert entries["frc1"]["streak_length"] == 5
    assert entries["frc1"]["is_active"] is True


def test_tie_does_not_break_streak(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    _put_match("2024nyny", 2024, red_score=5, blue_score=5, match_number=2)  # tie
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=3)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    # Tie is neutral — streak is 2 wins, not broken
    assert entries["frc1"]["streak_length"] == 2
    assert entries["frc1"]["is_active"] is True


def test_tie_does_not_advance_streak(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    for _ in range(3):
        pass  # no wins
    _put_match("2024nyny", 2024, red_score=5, blue_score=5, match_number=1)  # tie only

    insights = compute_insights_for_year(0, [_calc()])
    # No wins recorded — no entries
    assert insights == []


def test_streak_crosses_years(ndb_stub) -> None:
    _put_event("2023nyny", 2023)
    for i in range(1, 4):
        _put_match("2023nyny", 2023, red_score=10, blue_score=5, match_number=i)

    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    # 3 wins in 2023 + 3 wins in 2024 = 6 consecutive wins
    assert entries["frc1"]["streak_length"] == 6
    assert entries["frc1"]["start"] == "2023nyny"
    assert entries["frc1"]["end"] == "2024nyny"
    assert entries["frc1"]["is_active"] is True


def test_loss_between_years_resets_cross_year_streak(ndb_stub) -> None:
    _put_event("2023nyny", 2023)
    for i in range(1, 4):
        _put_match("2023nyny", 2023, red_score=10, blue_score=5, match_number=i)
    # frc1 loses the last match of 2023
    _put_match("2023nyny", 2023, red_score=5, blue_score=10, match_number=4)

    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    # Best is 3 (from 2023 before the loss), not 6
    assert entries["frc1"]["streak_length"] == 3
    assert entries["frc1"]["start"] == "2023nyny"
    assert entries["frc1"]["is_active"] is False


def test_tie_bridges_wins_across_years(ndb_stub) -> None:
    _put_event("2023nyny", 2023)
    for i in range(1, 4):
        _put_match("2023nyny", 2023, red_score=10, blue_score=5, match_number=i)
    # Tie at end of 2023 — neutral, does not break streak
    _put_match("2023nyny", 2023, red_score=5, blue_score=5, match_number=4)

    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    # 3 wins + tie (neutral) + 3 wins = streak of 6 wins
    assert entries["frc1"]["streak_length"] == 6
    assert entries["frc1"]["is_active"] is True


def test_cancelled_event_does_not_break_streak(ndb_stub) -> None:
    _put_event("2019nyny", 2019)
    for i in range(1, 4):
        _put_match("2019nyny", 2019, red_score=10, blue_score=5, match_number=i)

    _put_event("2020nyny", 2020)  # cancelled, no matches

    _put_event("2022nyny", 2022)
    for i in range(1, 3):
        _put_match("2022nyny", 2022, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 5
    assert entries["frc1"]["start"] == "2019nyny"
    assert entries["frc1"]["end"] == "2022nyny"
    assert entries["frc1"]["is_active"] is True


def test_unplayed_matches_are_skipped(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    Match(
        id="2024nyny_qm2",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, "2024nyny"),
        year=2024,
        match_number=2,
        set_number=1,
        team_key_names=_ALL_TEAMS,
        alliances_json=_alliances_json(-1, -1),
    ).put()

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 1
    assert entries["frc1"]["is_active"] is True


def test_is_active_false_when_current_run_is_not_best(ndb_stub) -> None:
    _put_event("2023nyny", 2023)
    for i in range(1, 6):
        _put_match("2023nyny", 2023, red_score=10, blue_score=5, match_number=i)
    _put_match("2023nyny", 2023, red_score=5, blue_score=10, match_number=6)  # loss

    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 5
    assert entries["frc1"]["is_active"] is False
