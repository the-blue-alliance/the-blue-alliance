from datetime import datetime
from typing import List, Optional

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.clubs.world_championship_winners import (
    WorldChampionshipWinnersClubV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team


def _put_event(
    event_key: str,
    year: int,
    event_type: EventType,
    start_date: Optional[datetime] = None,
) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
        start_date=start_date,
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


def _winner_award(event_key: str, year: int, team_keys: List[str]) -> None:
    _put_award(event_key, year, team_keys, AwardType.WINNER, EventType.CMP_FINALS)


def test_cmp_finals_winner_creates_entry(ndb_stub) -> None:
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _winner_award("2024cmptx", 2024, ["frc254"])

    insights = compute_insights_for_year(
        0, [WorldChampionshipWinnersClubV2Calculator()]
    )

    assert len(insights) == 1
    insight = insights[0]
    assert insight.key_name == "0_v2_clubs_world_championship_winners"
    assert insight.name == "world_championship_winners"
    assert insight.display_name == "World Championship Winners"
    assert insight.category == "clubs"
    assert insight.data["context_type"] == "none"
    assert insight.data["entries"] == [
        {"team_key": "frc254", "event_added_key": "2024cmptx"}
    ]


def test_all_winning_teams_recorded(ndb_stub) -> None:
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _winner_award("2024cmptx", 2024, ["frc254", "frc1323", "frc604"])

    insights = compute_insights_for_year(
        0, [WorldChampionshipWinnersClubV2Calculator()]
    )

    team_keys = [e["team_key"] for e in insights[0].data["entries"]]
    assert team_keys == ["frc254", "frc604", "frc1323"]


def test_non_cmp_finals_winner_ignored(ndb_stub) -> None:
    _put_event("2024arc", 2024, EventType.CMP_DIVISION)
    _put_award("2024arc", 2024, ["frc1"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2024casj", 2024, EventType.REGIONAL)
    _put_award("2024casj", 2024, ["frc2"], AwardType.WINNER, EventType.REGIONAL)

    insights = compute_insights_for_year(
        0, [WorldChampionshipWinnersClubV2Calculator()]
    )

    assert insights == []


def test_non_winner_award_at_cmp_finals_ignored(ndb_stub) -> None:
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _put_award("2024cmptx", 2024, ["frc1"], AwardType.CHAIRMANS, EventType.CMP_FINALS)

    insights = compute_insights_for_year(
        0, [WorldChampionshipWinnersClubV2Calculator()]
    )

    assert insights == []


def test_event_added_key_is_earliest(ndb_stub) -> None:
    _put_event("2011cmp", 2011, EventType.CMP_FINALS, start_date=datetime(2011, 4, 30))
    _winner_award("2011cmp", 2011, ["frc254"])
    _put_event("2008cmp", 2008, EventType.CMP_FINALS, start_date=datetime(2008, 4, 19))
    _winner_award("2008cmp", 2008, ["frc254"])

    insights = compute_insights_for_year(
        0, [WorldChampionshipWinnersClubV2Calculator()]
    )

    assert insights[0].data["entries"][0]["event_added_key"] == "2008cmp"


def test_no_insight_for_specific_year(ndb_stub) -> None:
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _winner_award("2024cmptx", 2024, ["frc254"])

    insights = compute_insights_for_year(
        2024, [WorldChampionshipWinnersClubV2Calculator()]
    )

    assert insights == []


def test_entries_sorted_by_team_number(ndb_stub) -> None:
    _put_event("2019cmp", 2019, EventType.CMP_FINALS)
    _winner_award("2019cmp", 2019, ["frc1114"])
    _put_event("2024cmptx", 2024, EventType.CMP_FINALS)
    _winner_award("2024cmptx", 2024, ["frc321"])

    insights = compute_insights_for_year(
        0, [WorldChampionshipWinnersClubV2Calculator()]
    )

    team_keys = [e["team_key"] for e in insights[0].data["entries"]]
    assert team_keys == ["frc321", "frc1114"]
