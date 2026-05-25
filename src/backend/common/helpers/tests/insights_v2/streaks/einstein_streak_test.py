from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.helpers.insights_v2.streaks.einstein_streak import (
    LongestEinsteinStreakV2Calculator,
)
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team

_ALLIANCES_JSON = (
    '{"red": {"score": 0, "teams": ["frc1", "frc2", "frc3"]},'
    ' "blue": {"score": 0, "teams": ["frc4", "frc5", "frc6"]}}'
)


def _put_event(event_key: str, year: int, event_type: EventType) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
    ).put()


def _put_winner_award(
    event_key: str, year: int, team_keys: list, event_type: EventType
) -> None:
    Award(
        id=f"{event_key}_1",
        year=year,
        award_type_enum=AwardType.WINNER,
        event_type_enum=event_type,
        event=ndb.Key(Event, event_key),
        name_str="Division Winners",
        team_list=[ndb.Key(Team, k) for k in team_keys],
    ).put()


def _put_match(event_key: str, year: int, team_keys: list) -> None:
    Match(
        id=f"{event_key}_qm1",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, event_key),
        year=year,
        match_number=1,
        set_number=1,
        team_key_names=team_keys,
        alliances_json=_ALLIANCES_JSON,
    ).put()


def test_single_division_win_creates_streak_of_1(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp1", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp1", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["key_type"] == "team"
    assert top["streak_length"] == 1
    assert top["start"] == "2022"
    assert top["end"] == "2022"
    assert top["is_active"] is True


def test_consecutive_wins_build_streak(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp1", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp1", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_winner_award("2023micmp1", 2023, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2023micmp1", 2023, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["streak_length"] == 2
    assert top["start"] == "2022"
    assert top["end"] == "2023"
    assert top["is_active"] is True


def test_streak_reset_when_team_does_not_attend_cmp(ndb_stub) -> None:
    # frc254 wins in 2022; in 2023 there are CMP_DIVISION events but frc254 is absent.
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp1", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp1", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_winner_award("2023micmp1", 2023, ["frc1"], EventType.CMP_DIVISION)
    _put_match("2023micmp1", 2023, ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    frc254_entry = next(e for e in insights[0].data["entries"] if e["key"] == "frc254")
    assert frc254_entry["streak_length"] == 1
    assert frc254_entry["start"] == "2022"
    assert frc254_entry["end"] == "2022"
    assert frc254_entry["is_active"] is False


def test_streak_reset_when_team_attends_but_does_not_win(ndb_stub) -> None:
    # frc254 wins in 2022; in 2023 they attend but another alliance wins.
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp1", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp1", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_winner_award("2023micmp1", 2023, ["frc1"], EventType.CMP_DIVISION)
    _put_match("2023micmp1", 2023, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    frc254_entry = next(e for e in insights[0].data["entries"] if e["key"] == "frc254")
    assert frc254_entry["streak_length"] == 1
    assert frc254_entry["is_active"] is False


def test_no_cmp_divisions_preserves_streak(ndb_stub) -> None:
    # Wins in 2019; 2020/2021 had no CMP events (COVID); wins again in 2022.
    _put_event("2019micmp1", 2019, EventType.CMP_DIVISION)
    _put_winner_award("2019micmp1", 2019, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2019micmp1", 2019, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp1", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp1", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["streak_length"] == 2
    assert top["start"] == "2019"
    assert top["end"] == "2022"
    assert top["is_active"] is True


def test_non_cmp_division_winner_award_ignored(ndb_stub) -> None:
    # WINNER at a CMP_FINALS event should not count toward the Einstein streak.
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_winner_award("2022cmptx", 2022, ["frc254"], EventType.CMP_FINALS)
    _put_match("2022cmptx", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])
    assert insights == []


def test_cancelled_cmp_division_does_not_break_streak(ndb_stub) -> None:
    # A CMP_DIVISION event with no matches is treated as cancelled.
    _put_event("2019micmp1", 2019, EventType.CMP_DIVISION)
    _put_winner_award("2019micmp1", 2019, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2019micmp1", 2019, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    # Cancelled — no matches
    _put_event("2020micmp1", 2020, EventType.CMP_DIVISION)

    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp1", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp1", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["streak_length"] == 2
    assert top["start"] == "2019"
    assert top["end"] == "2022"
    assert top["is_active"] is True


def test_winning_multiple_divisions_same_year_counts_once(ndb_stub) -> None:
    # A team winning two different CMP divisions in the same year counts as one streak year.
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp1", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp1", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    _put_event("2022micmp2", 2022, EventType.CMP_DIVISION)
    _put_winner_award("2022micmp2", 2022, ["frc254"], EventType.CMP_DIVISION)
    _put_match("2022micmp2", 2022, ["frc254", "frc7", "frc8", "frc9", "frc10", "frc11"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["streak_length"] == 1


def test_team_with_two_equal_streaks_appears_twice(ndb_stub) -> None:
    # frc254 wins 2018 and 2019 (streak of 2), loses in 2020,
    # then wins 2022 and 2023 (another streak of 2).
    # Both streaks should appear in the output.
    for year, event_key in [(2018, "2018micmp1"), (2019, "2019micmp1")]:
        _put_event(event_key, year, EventType.CMP_DIVISION)
        _put_winner_award(event_key, year, ["frc254"], EventType.CMP_DIVISION)
        _put_match(event_key, year, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    # 2020: CMP_DIVISION exists but frc1 wins, not frc254 — breaks frc254's streak
    _put_event("2020micmp1", 2020, EventType.CMP_DIVISION)
    _put_winner_award("2020micmp1", 2020, ["frc1"], EventType.CMP_DIVISION)
    _put_match("2020micmp1", 2020, ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"])

    for year, event_key in [(2022, "2022micmp1"), (2023, "2023micmp1")]:
        _put_event(event_key, year, EventType.CMP_DIVISION)
        _put_winner_award(event_key, year, ["frc254"], EventType.CMP_DIVISION)
        _put_match(event_key, year, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(0, [LongestEinsteinStreakV2Calculator()])

    assert len(insights) == 1
    frc254_entries = [e for e in insights[0].data["entries"] if e["key"] == "frc254"]
    assert len(frc254_entries) == 2
    assert all(e["streak_length"] == 2 for e in frc254_entries)
    starts = {e["start"] for e in frc254_entries}
    assert starts == {"2018", "2022"}
