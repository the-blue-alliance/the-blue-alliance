from typing import List

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.leaderboards.most_cmp_wins import (
    MostCmpWinsV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team


def _put_event(event_key: str, year: int, event_type: EventType) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
    ).put()


def _put_award(
    event_key: str,
    year: int,
    team_keys: List[str],
    award_type: AwardType,
    event_type: EventType,
) -> None:
    Award(
        id=f"{event_key}_{award_type.value}",
        year=year,
        award_type_enum=award_type,
        event_type_enum=event_type,
        event=ndb.Key(Event, event_key),
        name_str=str(award_type),
        team_list=[ndb.Key(Team, k) for k in team_keys],
    ).put()


def test_single_win_excluded(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(2022, [MostCmpWinsV2Calculator()])

    assert len(insights) == 1
    assert insights[0].data["rankings"] == []


def test_two_wins_shown_in_rankings(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpWinsV2Calculator()])

    assert insights[0].data["rankings"][0]["keys"] == ["frc254"]
    assert insights[0].data["rankings"][0]["value"] == 2


def test_context_event_keys(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpWinsV2Calculator()])

    assert insights[0].data["context_type"] == "event_list"
    ranking = insights[0].data["rankings"][0]
    assert ranking["contexts"] == [{"event_keys": ["2022cmptx", "2023cmptx"]}]


def test_finalist_does_not_count(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.FINALIST, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.FINALIST, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpWinsV2Calculator()])

    assert len(insights) == 0


def test_division_event_ignored(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award("2023micmp1", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(0, [MostCmpWinsV2Calculator()])

    assert len(insights) == 0


def test_key_name(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(2022, [MostCmpWinsV2Calculator()])

    assert insights[0].key_name == "2022_v2_leaderboard_most_cmp_wins"


def test_insight_name_and_display_name(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(2022, [MostCmpWinsV2Calculator()])

    assert insights[0].name == "most_cmp_wins"
    assert insights[0].display_name == "Most World Championship Wins"


def test_multiple_teams_same_alliance_each_counted(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award(
        "2022cmptx",
        2022,
        ["frc1", "frc2", "frc3"],
        AwardType.WINNER,
        EventType.CMP_FINALS,
    )
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award(
        "2023cmptx",
        2023,
        ["frc1", "frc2", "frc3"],
        AwardType.WINNER,
        EventType.CMP_FINALS,
    )

    insights = compute_insights_for_year(0, [MostCmpWinsV2Calculator()])

    ranking = insights[0].data["rankings"][0]
    assert set(ranking["keys"]) == {"frc1", "frc2", "frc3"}
    assert ranking["value"] == 2


def test_rankings_sorted_descending_by_count(ndb_stub) -> None:
    # frc1 wins 3 times, frc2 wins 2 times
    for event_key, year in [
        ("2021cmptx", 2021),
        ("2022cmptx", 2022),
        ("2023cmptx", 2023),
    ]:
        _put_event(event_key, year, EventType.CMP_FINALS)
        _put_award(event_key, year, ["frc1"], AwardType.WINNER, EventType.CMP_FINALS)

    for event_key, year in [("2024cmptx", 2024), ("2025cmptx", 2025)]:
        _put_event(event_key, year, EventType.CMP_FINALS)
        _put_award(event_key, year, ["frc2"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpWinsV2Calculator()])

    rankings = insights[0].data["rankings"]
    assert rankings[0]["keys"] == ["frc1"]
    assert rankings[0]["value"] == 3
    assert rankings[1]["keys"] == ["frc2"]
    assert rankings[1]["value"] == 2
