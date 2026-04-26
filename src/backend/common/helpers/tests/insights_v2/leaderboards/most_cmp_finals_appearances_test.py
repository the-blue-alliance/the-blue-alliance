from typing import List

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.leaderboards.most_cmp_finals_appearances import (
    MostCmpFinalsAppearancesV2Calculator,
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


def test_single_appearance_excluded(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(2022, [MostCmpFinalsAppearancesV2Calculator()])

    assert len(insights) == 1
    assert insights[0].data["rankings"] == []


def test_two_appearances_shown_in_rankings(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpFinalsAppearancesV2Calculator()])

    assert insights[0].data["rankings"][0]["keys"] == ["frc254"]
    assert insights[0].data["rankings"][0]["value"] == 2


def test_context_event_keys(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.FINALIST, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpFinalsAppearancesV2Calculator()])

    assert insights[0].data["context_type"] == "event_list"
    ranking = insights[0].data["rankings"][0]
    assert ranking["contexts"] == [{"event_keys": ["2022cmptx", "2023cmptx"]}]


def test_finalist_and_winner_both_count(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.FINALIST, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpFinalsAppearancesV2Calculator()])

    assert insights[0].data["rankings"][0]["value"] == 2


def test_division_event_ignored(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award("2023micmp1", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(0, [MostCmpFinalsAppearancesV2Calculator()])

    assert len(insights) == 0


def test_non_finals_award_ignored(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.CHAIRMANS, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.CHAIRMANS, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpFinalsAppearancesV2Calculator()])

    assert len(insights) == 0


def test_key_name(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(2022, [MostCmpFinalsAppearancesV2Calculator()])

    assert insights[0].key_name == "2022_v2_leaderboard_most_cmp_finals_appearances"


def test_insight_name_and_display_name(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(2022, [MostCmpFinalsAppearancesV2Calculator()])

    assert insights[0].name == "most_cmp_finals_appearances"
    assert insights[0].display_name == "Most World Championship Finals Appearances"


def test_multiple_cmp_finals_same_year(ndb_stub) -> None:
    # In some years there were two separate World Championships (e.g. Detroit & Houston)
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2022cmpmi", 2022, EventType.CMP_FINALS)
    _put_award("2022cmpmi", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(0, [MostCmpFinalsAppearancesV2Calculator()])

    assert insights[0].data["rankings"][0]["value"] == 3
    assert insights[0].data["rankings"][0]["contexts"] == [
        {"event_keys": ["2022cmpmi", "2022cmptx", "2023cmptx"]}
    ]
