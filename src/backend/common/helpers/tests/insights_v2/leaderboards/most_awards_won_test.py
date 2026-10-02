from typing import List

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.leaderboards.most_awards_won import (
    MostAwardsWonV2Calculator,
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


def test_single_award_excluded(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.WINNER, EventType.REGIONAL)

    insights = compute_insights_for_year(2022, [MostAwardsWonV2Calculator()])

    assert len(insights) == 0


def test_multiple_awards_accumulate(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.WINNER, EventType.REGIONAL)
    _put_award(
        "2022nytr",
        2022,
        ["frc254"],
        AwardType.ENGINEERING_INSPIRATION,
        EventType.REGIONAL,
    )

    insights = compute_insights_for_year(2022, [MostAwardsWonV2Calculator()])

    assert insights[0].data["rankings"][0]["keys"] == ["frc254"]
    assert insights[0].data["rankings"][0]["value"] == 2


def test_awards_counted_across_events(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2023nytr", 2023, EventType.REGIONAL)
    _put_award("2023nytr", 2023, ["frc254"], AwardType.CHAIRMANS, EventType.REGIONAL)

    insights = compute_insights_for_year(0, [MostAwardsWonV2Calculator()])

    assert insights[0].data["rankings"][0]["keys"] == ["frc254"]
    assert insights[0].data["rankings"][0]["value"] == 2


def test_all_award_types_counted(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.WINNER, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.FINALIST, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.CHAIRMANS, EventType.REGIONAL)

    insights = compute_insights_for_year(2022, [MostAwardsWonV2Calculator()])

    assert insights[0].data["rankings"][0]["value"] == 3


def test_different_teams_separate_counts(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1"], AwardType.WINNER, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1"], AwardType.CHAIRMANS, EventType.REGIONAL)
    _put_award(
        "2022nytr",
        2022,
        ["frc1"],
        AwardType.ENGINEERING_INSPIRATION,
        EventType.REGIONAL,
    )
    _put_award("2022nytr", 2022, ["frc2"], AwardType.QUALITY, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc2"], AwardType.SAFETY, EventType.REGIONAL)

    insights = compute_insights_for_year(2022, [MostAwardsWonV2Calculator()])

    rankings = insights[0].data["rankings"]
    assert rankings[0]["keys"] == ["frc1"]
    assert rankings[0]["value"] == 3
    assert rankings[1]["keys"] == ["frc2"]
    assert rankings[1]["value"] == 2


def test_key_name(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.WINNER, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.CHAIRMANS, EventType.REGIONAL)

    insights = compute_insights_for_year(2022, [MostAwardsWonV2Calculator()])

    assert insights[0].key_name == "2022_v2_leaderboard_most_awards_won"


def test_insight_name_and_display_name(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.WINNER, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.CHAIRMANS, EventType.REGIONAL)

    insights = compute_insights_for_year(2022, [MostAwardsWonV2Calculator()])

    assert insights[0].name == "most_awards_won"
    assert insights[0].display_name == "Most Awards Won"
