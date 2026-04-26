from typing import List

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.leaderboards.most_division_finals_appearances import (
    MostDivisionFinalsAppearancesV2Calculator,
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


def test_single_event_excluded(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(
        2022, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert len(insights) == 1
    assert insights[0].data["rankings"] == []


def test_two_events_shown_in_rankings(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award("2023micmp1", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert len(insights) == 1
    assert insights[0].data["rankings"][0]["keys"] == ["frc254"]
    assert insights[0].data["rankings"][0]["value"] == 2


def test_context_event_keys(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award(
        "2023micmp1", 2023, ["frc254"], AwardType.FINALIST, EventType.CMP_DIVISION
    )

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert insights[0].data["context_type"] == "event_list"
    ranking = insights[0].data["rankings"][0]
    assert ranking["contexts"] == [{"event_keys": ["2022micmp1", "2023micmp1"]}]


def test_finalist_and_winner_both_count(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award(
        "2023micmp1", 2023, ["frc254"], AwardType.FINALIST, EventType.CMP_DIVISION
    )

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert insights[0].data["rankings"][0]["value"] == 2


def test_non_division_event_ignored(ndb_stub) -> None:
    _put_event("2022cmptx", 2022, EventType.CMP_FINALS)
    _put_award("2022cmptx", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)
    _put_event("2023cmptx", 2023, EventType.CMP_FINALS)
    _put_award("2023cmptx", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_FINALS)

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert len(insights) == 0


def test_non_finals_award_ignored(ndb_stub) -> None:
    award_type = AwardType.CHAIRMANS
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], award_type, EventType.CMP_DIVISION)
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award("2023micmp1", 2023, ["frc254"], award_type, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert len(insights) == 0


def test_deduplication_per_event(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)
    Award(
        id="2022micmp1_1_dupe",
        year=2022,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.CMP_DIVISION,
        event=ndb.Key(Event, "2022micmp1"),
        name_str="duplicate",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award("2023micmp1", 2023, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert insights[0].data["rankings"][0]["value"] == 2


def test_key_name(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(
        2022, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert (
        insights[0].key_name == "2022_v2_leaderboard_most_division_finals_appearances"
    )


def test_insight_name_and_display_name(ndb_stub) -> None:
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc254"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(
        2022, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert insights[0].name == "most_division_finals_appearances"
    assert insights[0].display_name == "Most Division Finals Appearances"


def test_tied_teams_have_separate_contexts(ndb_stub) -> None:
    # frc1 and frc2 each have 2 appearances but at different events
    _put_event("2022micmp1", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp1", 2022, ["frc1"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2022micmp2", 2022, EventType.CMP_DIVISION)
    _put_award("2022micmp2", 2022, ["frc1"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2023micmp1", 2023, EventType.CMP_DIVISION)
    _put_award("2023micmp1", 2023, ["frc2"], AwardType.WINNER, EventType.CMP_DIVISION)
    _put_event("2023micmp2", 2023, EventType.CMP_DIVISION)
    _put_award("2023micmp2", 2023, ["frc2"], AwardType.WINNER, EventType.CMP_DIVISION)

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    ranking = insights[0].data["rankings"][0]
    assert ranking["keys"] == ["frc1", "frc2"]
    assert ranking["value"] == 2
    # Each team has its own context — not a shared union
    frc1_ctx, frc2_ctx = ranking["contexts"]
    assert frc1_ctx["event_keys"] == ["2022micmp1", "2022micmp2"]
    assert frc2_ctx["event_keys"] == ["2023micmp1", "2023micmp2"]


def test_teams_sorted_numerically_within_group(ndb_stub) -> None:
    for event_key, year in [("2022micmp1", 2022), ("2023micmp1", 2023)]:
        _put_event(event_key, year, EventType.CMP_DIVISION)
        for team in ["frc100", "frc5", "frc50"]:
            Award(
                id=f"{event_key}_1_{team}",
                year=year,
                award_type_enum=AwardType.WINNER,
                event_type_enum=EventType.CMP_DIVISION,
                event=ndb.Key(Event, event_key),
                name_str="winner",
                team_list=[ndb.Key(Team, team)],
            ).put()

    insights = compute_insights_for_year(
        0, [MostDivisionFinalsAppearancesV2Calculator()]
    )

    assert insights[0].data["rankings"][0]["keys"] == ["frc5", "frc50", "frc100"]
