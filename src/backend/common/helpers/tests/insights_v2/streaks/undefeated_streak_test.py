import json
from datetime import datetime
from typing import Optional

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.helpers.insights_v2.streaks.undefeated_streak import (
    LongestUndefeatedStreakV2Calculator,
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
    event_key: str,
    year: int,
    event_type: EventType = EventType.REGIONAL,
    start_date: Optional[datetime] = None,
) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
        start_date=start_date,
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


def _calc() -> LongestUndefeatedStreakV2Calculator:
    return LongestUndefeatedStreakV2Calculator()


def test_consecutive_wins_build_streak(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=2)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=3)

    insights = compute_insights_for_year(0, [_calc()])
    assert len(insights) == 1
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 3
    assert entries["frc1"]["start"] == "2024nyny"
    assert entries["frc1"]["end"] == "2024nyny"
    assert entries["frc1"]["is_active"] is True

    # Blue lost all 3 — no entry for blue teams
    assert "frc4" not in entries


def test_loss_ends_streak_subsequent_wins_ignored(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    # frc1 (red) wins 2, loses 1, then wins 10 more
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=2)
    _put_match("2024nyny", 2024, red_score=5, blue_score=10, match_number=3)
    for i in range(4, 14):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 2
    assert entries["frc1"]["is_active"] is False


def test_loss_on_first_match_gives_no_streak(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    # frc1 (red) loses first, then wins 10
    _put_match("2024nyny", 2024, red_score=5, blue_score=10, match_number=1)
    for i in range(2, 12):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    if insights:
        entries = {e["key"]: e for e in insights[0].data["entries"]}
        assert "frc1" not in entries


def test_tie_counts_as_non_loss(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    # frc1: win, tie, win — streak should be 3
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    _put_match("2024nyny", 2024, red_score=5, blue_score=5, match_number=2)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=3)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 3
    assert entries["frc1"]["is_active"] is True


def test_tie_after_loss_does_not_restart_streak(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    _put_match("2024nyny", 2024, red_score=5, blue_score=10, match_number=2)  # loss
    _put_match("2024nyny", 2024, red_score=5, blue_score=5, match_number=3)  # tie

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 1
    assert entries["frc1"]["is_active"] is False


def test_streak_resets_each_year(ndb_stub) -> None:
    # frc1 wins 5 in 2023, then wins 3 in 2024 — best is 5, not 8
    _put_event("2023nyny", 2023)
    for i in range(1, 6):
        _put_match("2023nyny", 2023, red_score=10, blue_score=5, match_number=i)

    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 5
    assert entries["frc1"]["start"] == "2023nyny"
    assert entries["frc1"]["end"] == "2023nyny"
    # Current active run (3) is less than best (5)
    assert entries["frc1"]["is_active"] is False


def test_best_streak_preserved_after_later_loss(ndb_stub) -> None:
    # frc1 goes 5-0 in 2018, then loses first match of 2019 — streak stays 5
    _put_event("2018nyny", 2018)
    for i in range(1, 6):
        _put_match("2018nyny", 2018, red_score=10, blue_score=5, match_number=i)

    _put_event("2019nyny", 2019)
    _put_match("2019nyny", 2019, red_score=5, blue_score=10, match_number=1)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 5
    assert entries["frc1"]["start"] == "2018nyny"
    assert entries["frc1"]["is_active"] is False


def test_cancelled_event_does_not_break_streak(ndb_stub) -> None:
    _put_event("2019nyny", 2019)
    for i in range(1, 4):
        _put_match("2019nyny", 2019, red_score=10, blue_score=5, match_number=i)

    # 2020 cancelled — no matches
    _put_event("2020nyny", 2020)

    _put_event("2022nyny", 2022)
    _put_match("2022nyny", 2022, red_score=5, blue_score=10, match_number=1)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 3
    assert entries["frc1"]["is_active"] is False


def test_unplayed_matches_are_skipped(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=1)
    # score of -1 means unplayed
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

    # Only the played match counts
    assert entries["frc1"]["streak_length"] == 1
    assert entries["frc1"]["is_active"] is True


def test_streak_spans_multiple_events_in_same_year(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    _put_event("2024mabos", 2024, EventType.DISTRICT)
    for i in range(1, 4):
        _put_match("2024mabos", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 6
    # mabos < nyny alphabetically, so mabos is fetched first in test stub
    assert entries["frc1"]["start"] == "2024mabos"
    assert entries["frc1"]["end"] == "2024nyny"
    assert entries["frc1"]["is_active"] is True


def test_all_season_event_types_count(ndb_stub) -> None:
    # CMP_DIVISION wins count toward the streak
    _put_event("2024cmptx", 2024, EventType.CMP_DIVISION)
    for i in range(1, 4):
        _put_match("2024cmptx", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 3


def test_is_active_true_when_current_run_equals_best(ndb_stub) -> None:
    # frc1 goes 3-0 across two years; 2023 run (2) and 2024 run (3) — best is 3, active
    _put_event("2023nyny", 2023)
    for i in range(1, 3):
        _put_match("2023nyny", 2023, red_score=10, blue_score=5, match_number=i)
    # frc1 then loses in 2023
    _put_match("2023nyny", 2023, red_score=5, blue_score=10, match_number=3)

    _put_event("2024nyny", 2024)
    for i in range(1, 4):
        _put_match("2024nyny", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 3
    assert entries["frc1"]["start"] == "2024nyny"
    assert entries["frc1"]["is_active"] is True


def test_2015_playoff_match_winner_determined_by_score(ndb_stub) -> None:
    # 2015 non-finals playoff matches have winning_alliance="" in the model;
    # the calculator must use scores so the real winner advances and the loser resets.
    _put_event("2015nyny", 2015)
    # frc1 (red) wins; without the fix, winning_alliance="" would advance frc4 too
    Match(
        id="2015nyny_sf1m1",
        comp_level=CompLevel.SF,
        event=ndb.Key(Event, "2015nyny"),
        year=2015,
        match_number=1,
        set_number=1,
        team_key_names=_ALL_TEAMS,
        alliances_json=_alliances_json(red_score=200, blue_score=100),
    ).put()

    insights = compute_insights_for_year(0, [_calc()])
    assert len(insights) == 1
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 1
    assert "frc4" not in entries


def test_2015_playoff_loss_ends_undefeated_streak(ndb_stub) -> None:
    _put_event("2015nyny", 2015)
    # frc1 wins match 1, then loses match 2 — streak ends at 1
    Match(
        id="2015nyny_sf1m1",
        comp_level=CompLevel.SF,
        event=ndb.Key(Event, "2015nyny"),
        year=2015,
        match_number=1,
        set_number=1,
        team_key_names=_ALL_TEAMS,
        alliances_json=_alliances_json(red_score=200, blue_score=100),
    ).put()
    Match(
        id="2015nyny_sf1m2",
        comp_level=CompLevel.SF,
        event=ndb.Key(Event, "2015nyny"),
        year=2015,
        match_number=2,
        set_number=1,
        team_key_names=_ALL_TEAMS,
        alliances_json=_alliances_json(red_score=50, blue_score=150),
    ).put()

    insights = compute_insights_for_year(0, [_calc()])
    entries = {e["key"]: e for e in insights[0].data["entries"]}

    assert entries["frc1"]["streak_length"] == 1
    assert entries["frc1"]["is_active"] is False


def test_events_processed_in_start_date_order(ndb_stub) -> None:
    # 2024zzzy is alphabetically later but starts earlier (week 1).
    # A loss there must end the undefeated streak even though 2024aaax comes
    # first alphabetically. With start_date sorting, zzzy is processed first.
    week1 = datetime(2024, 3, 1)
    week2 = datetime(2024, 3, 8)

    _put_event("2024zzzy", 2024, start_date=week1)
    _put_match("2024zzzy", 2024, red_score=5, blue_score=10, match_number=1)  # loss

    _put_event("2024aaax", 2024, start_date=week2)
    for i in range(1, 4):
        _put_match("2024aaax", 2024, red_score=10, blue_score=5, match_number=i)

    insights = compute_insights_for_year(0, [_calc()])
    if insights:
        entries = {e["key"]: e for e in insights[0].data["entries"]}
        # frc1 lost at zzzy (week 1) so has no undefeated streak for this year
        assert "frc1" not in entries
