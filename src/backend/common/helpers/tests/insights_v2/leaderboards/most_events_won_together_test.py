from datetime import datetime
from typing import List, Optional

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.leaderboards.most_events_won_together import (
    MostEventsWonTogetherV2Calculator,
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


def test_single_event_win_excluded(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award(
        "2022nytr", 2022, ["frc1", "frc2", "frc3"], AwardType.WINNER, EventType.REGIONAL
    )

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    assert len(insights) == 0


def test_pair_count_increments(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award(
        "2022nytr", 2022, ["frc1", "frc2", "frc3"], AwardType.WINNER, EventType.REGIONAL
    )
    _put_event("2023nytr", 2023, EventType.REGIONAL)
    _put_award(
        "2023nytr", 2023, ["frc1", "frc2", "frc3"], AwardType.WINNER, EventType.REGIONAL
    )

    insights = compute_insights_for_year(0, [MostEventsWonTogetherV2Calculator()])

    assert insights[0].data["rankings"][0]["value"] == 2


def test_pair_key_format_ascending_order(ndb_stub) -> None:
    for event_key, year in [("2022nytr", 2022), ("2023nytr", 2023)]:
        _put_event(event_key, year, EventType.REGIONAL)
        _put_award(
            event_key, year, ["frc300", "frc100"], AwardType.WINNER, EventType.REGIONAL
        )

    insights = compute_insights_for_year(0, [MostEventsWonTogetherV2Calculator()])

    for ranking in insights[0].data["rankings"]:
        for pair in ranking["keys"]:
            team_a, team_b = pair
            assert int(team_a[3:]) < int(team_b[3:]), "pair not in ascending order"


def test_finalist_does_not_count(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award(
        "2022nytr",
        2022,
        ["frc1", "frc2"],
        AwardType.FINALIST,
        EventType.REGIONAL,
    )

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    assert len(insights) == 0


def test_all_season_event_types_counted(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2022micmp", 2022, EventType.DISTRICT_CMP)
    _put_award(
        "2022micmp", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.DISTRICT_CMP
    )

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    assert insights[0].data["rankings"][0]["value"] == 2


def test_different_pairs_below_min_count_excluded(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2023nytr", 2023, EventType.REGIONAL)
    _put_award("2023nytr", 2023, ["frc3", "frc4"], AwardType.WINNER, EventType.REGIONAL)

    insights = compute_insights_for_year(0, [MostEventsWonTogetherV2Calculator()])

    assert len(insights) == 0


def test_key_name(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2022txcmp", 2022, EventType.DISTRICT_CMP)
    _put_award(
        "2022txcmp", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.DISTRICT_CMP
    )

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    assert insights[0].key_name == "2022_v2_leaderboard_most_events_won_together"


def test_insight_name_and_display_name(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2022txcmp", 2022, EventType.DISTRICT_CMP)
    _put_award(
        "2022txcmp", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.DISTRICT_CMP
    )

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    assert insights[0].name == "most_events_won_together"
    assert insights[0].display_name == "Most Events Won Together"


def test_context_type_is_event_list(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2022txcmp", 2022, EventType.DISTRICT_CMP)
    _put_award(
        "2022txcmp", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.DISTRICT_CMP
    )

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    assert insights[0].data["context_type"] == "event_list"


def test_event_list_context_contains_event_keys(ndb_stub) -> None:
    _put_event("2022nytr", 2022, EventType.REGIONAL)
    _put_award("2022nytr", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.REGIONAL)
    _put_event("2022txcmp", 2022, EventType.DISTRICT_CMP)
    _put_award(
        "2022txcmp", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.DISTRICT_CMP
    )

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    ranking = insights[0].data["rankings"][0]
    assert ranking["contexts"][0]["event_keys"] == ["2022nytr", "2022txcmp"]


def test_event_list_context_sorted_by_start_date(ndb_stub) -> None:
    # 2022txcmp starts later alphabetically but comes first chronologically.
    # The context event list should follow date order, not alphabetical order.
    _put_event(
        "2022txcmp", 2022, EventType.DISTRICT_CMP, start_date=datetime(2022, 3, 1)
    )
    _put_award(
        "2022txcmp", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.DISTRICT_CMP
    )
    _put_event("2022nytr", 2022, EventType.REGIONAL, start_date=datetime(2022, 4, 1))
    _put_award("2022nytr", 2022, ["frc1", "frc2"], AwardType.WINNER, EventType.REGIONAL)

    insights = compute_insights_for_year(2022, [MostEventsWonTogetherV2Calculator()])

    ranking = insights[0].data["rankings"][0]
    # txcmp (March) should precede nytr (April) despite being later alphabetically
    assert ranking["contexts"][0]["event_keys"] == ["2022txcmp", "2022nytr"]
