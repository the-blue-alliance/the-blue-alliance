from typing import List

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.leaderboards.most_district_cmp_wins import (
    MostDistrictCmpWinsV2Calculator,
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
    _put_event("2022micmp", 2022, EventType.DISTRICT_CMP)
    _put_award("2022micmp", 2022, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)

    insights = compute_insights_for_year(2022, [MostDistrictCmpWinsV2Calculator()])

    assert len(insights) == 0


def test_two_wins_included(ndb_stub) -> None:
    _put_event("2022micmp", 2022, EventType.DISTRICT_CMP)
    _put_award("2022micmp", 2022, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)
    _put_event("2023micmp", 2023, EventType.DISTRICT_CMP)
    _put_award("2023micmp", 2023, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)

    insights = compute_insights_for_year(0, [MostDistrictCmpWinsV2Calculator()])

    assert insights[0].data["rankings"][0]["keys"] == ["frc254"]
    assert insights[0].data["rankings"][0]["value"] == 2


def test_context_event_keys(ndb_stub) -> None:
    _put_event("2022micmp", 2022, EventType.DISTRICT_CMP)
    _put_award("2022micmp", 2022, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)
    _put_event("2023micmp", 2023, EventType.DISTRICT_CMP)
    _put_award("2023micmp", 2023, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)

    insights = compute_insights_for_year(0, [MostDistrictCmpWinsV2Calculator()])

    assert insights[0].data["context_type"] == "event_list"
    ranking = insights[0].data["rankings"][0]
    assert ranking["contexts"] == [{"event_keys": ["2022micmp", "2023micmp"]}]


def test_finalist_does_not_count(ndb_stub) -> None:
    _put_event("2022micmp", 2022, EventType.DISTRICT_CMP)
    _put_award(
        "2022micmp", 2022, ["frc254"], AwardType.FINALIST, EventType.DISTRICT_CMP
    )
    _put_event("2023micmp", 2023, EventType.DISTRICT_CMP)
    _put_award(
        "2023micmp", 2023, ["frc254"], AwardType.FINALIST, EventType.DISTRICT_CMP
    )

    insights = compute_insights_for_year(0, [MostDistrictCmpWinsV2Calculator()])

    assert len(insights) == 0


def test_non_district_cmp_event_ignored(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc254"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(2022, [MostDistrictCmpWinsV2Calculator()])

    assert len(insights) == 0


def test_key_name(ndb_stub) -> None:
    _put_event("2022micmp", 2022, EventType.DISTRICT_CMP)
    _put_award("2022micmp", 2022, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)
    _put_event("2023micmp", 2023, EventType.DISTRICT_CMP)
    _put_award("2023micmp", 2023, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)

    insights = compute_insights_for_year(0, [MostDistrictCmpWinsV2Calculator()])

    assert insights[0].key_name == "0_v2_leaderboard_most_district_cmp_wins"


def test_insight_name_and_display_name(ndb_stub) -> None:
    _put_event("2022micmp", 2022, EventType.DISTRICT_CMP)
    _put_award("2022micmp", 2022, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)
    _put_event("2023micmp", 2023, EventType.DISTRICT_CMP)
    _put_award("2023micmp", 2023, ["frc254"], AwardType.WINNER, EventType.DISTRICT_CMP)

    insights = compute_insights_for_year(0, [MostDistrictCmpWinsV2Calculator()])

    assert insights[0].name == "most_district_cmp_wins"
    assert insights[0].display_name == "Most District Championship Wins"
