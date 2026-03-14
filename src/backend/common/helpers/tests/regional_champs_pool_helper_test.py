import json

import pytest
from pyre_extensions import none_throws

from backend.common.helpers.regional_champs_pool_helper import (
    DistrictRankingTeamTotal,
    RegionalChampsPoolHelper,
    RegionalChampsPoolTiebreakers,
)
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.team import Team


@pytest.mark.parametrize(
    "event_key",
    [
        "2025mndu",
        "2025mndu2",
    ],
)
def test_calc_event_points(
    event_key, ndb_stub, setup_full_event, test_data_importer
) -> None:
    setup_full_event(event_key)

    event = Event.get_by_id(event_key)
    assert event is not None
    event_points = RegionalChampsPoolHelper.calculate_event_points(event)

    with open(
        test_data_importer._get_path(
            __file__, f"data/{event_key}_regional_champs_pool_points.json"
        ),
        "r",
    ) as f:
        expected_event_points = json.load(f)

    assert event_points == expected_event_points


def test_calc_multi_event_rankings_all_teams_filtered(setup_full_event) -> None:
    setup_full_event("2025mndu")
    setup_full_event("2025mndu2")

    events = [
        none_throws(Event.get_by_id("2025mndu")),
        none_throws(Event.get_by_id("2025mndu2")),
    ]

    rankings = RegionalChampsPoolHelper.calculate_rankings(events, [], 2025, None)
    assert rankings == {}


def test_calc_multi_event_rankings(setup_full_event) -> None:
    setup_full_event("2025mndu")
    setup_full_event("2025mndu2")

    events = [
        none_throws(Event.get_by_id("2025mndu")),
        none_throws(Event.get_by_id("2025mndu2")),
    ]

    teams = [
        none_throws(Team.get_by_id("frc2847")),
        none_throws(Team.get_by_id("frc2383")),
    ]

    rankings = RegionalChampsPoolHelper.calculate_rankings(events, teams, 2025, None)
    assert len(rankings) == 2
    assert rankings["frc2847"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=15,
                    award_points=5,
                    elim_points=30,
                    qual_points=21,
                    total=71,
                ),
            )
        ],
        point_total=128,
        qual_scores=[180, 161, 153],
        rookie_bonus=0,
        single_event_bonus=57,
        other_bonus=0,
        adjustments=0,
        tiebreakers=RegionalChampsPoolTiebreakers(
            best_playoff_points=30,
            best_alliance_points=15,
            best_qual_points=21,
        ),
    )
    assert rankings["frc2383"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[1],
                TeamAtEventDistrictPoints(
                    alliance_points=14,
                    award_points=45,
                    elim_points=20,
                    qual_points=19,
                    total=98,
                ),
            )
        ],
        point_total=171,
        qual_scores=[117, 101, 101],
        rookie_bonus=0,
        single_event_bonus=73,
        other_bonus=0,
        adjustments=0,
        tiebreakers=RegionalChampsPoolTiebreakers(
            best_playoff_points=20,
            best_alliance_points=14,
            best_qual_points=19,
        ),
    )


def test_hq_adjustments(setup_full_event) -> None:
    setup_full_event("2025mndu")

    events = [
        none_throws(Event.get_by_id("2025mndu")),
    ]

    teams = [
        none_throws(Team.get_by_id("frc2847")),
    ]

    rankings = RegionalChampsPoolHelper.calculate_rankings(
        events, teams, 2025, {"frc2847": 5}
    )
    assert len(rankings) == 1
    assert rankings["frc2847"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=15,
                    award_points=5,
                    elim_points=30,
                    qual_points=21,
                    total=71,
                ),
            )
        ],
        point_total=133,
        qual_scores=[180, 161, 153],
        rookie_bonus=0,
        single_event_bonus=57,
        other_bonus=0,
        adjustments=5,
        tiebreakers=RegionalChampsPoolTiebreakers(
            best_playoff_points=30,
            best_alliance_points=15,
            best_qual_points=21,
        ),
    )


def test_rookie_bonus_per_event(setup_full_event) -> None:
    """Test that rookie bonus is applied per event attended, not just once."""
    setup_full_event("2025mndu")
    setup_full_event("2025mndu2")

    events = [
        none_throws(Event.get_by_id("2025mndu")),
        none_throws(Event.get_by_id("2025mndu2")),
    ]

    # Set up event points for rookie teams that attend events
    # Rookie team attending both events
    event1_details = EventDetails.get_by_id("2025mndu")
    if event1_details and event1_details.regional_champs_pool_points:
        event1_details.regional_champs_pool_points["points"]["frc9001"] = (
            TeamAtEventDistrictPoints(
                alliance_points=10,
                award_points=0,
                elim_points=0,
                qual_points=15,
                total=25,
            )
        )
        event1_details.put()

    event2_details = EventDetails.get_by_id("2025mndu2")
    if event2_details and event2_details.regional_champs_pool_points:
        event2_details.regional_champs_pool_points["points"]["frc9001"] = (
            TeamAtEventDistrictPoints(
                alliance_points=12,
                award_points=0,
                elim_points=0,
                qual_points=18,
                total=30,
            )
        )
        event2_details.put()

    # Reload events to get updated points
    events = [
        none_throws(Event.get_by_id("2025mndu")),
        none_throws(Event.get_by_id("2025mndu2")),
    ]
    for event in events:
        event.prep_details()

    # Create rookie team
    rookie_two_events = Team(
        id="frc9001",
        team_number=9001,
        rookie_year=2025,  # Current year rookie gets 10 points per event
    )
    rookie_two_events.put()

    teams = [rookie_two_events]

    rankings = RegionalChampsPoolHelper.calculate_rankings(events, teams, 2025, None)

    # Rookie team attending 2 events should get 10 points per event = 20
    assert rankings["frc9001"]["rookie_bonus"] == 20
    # Total: 25 (event1) + 30 (event2) + 20 (rookie bonus) = 75
    assert rankings["frc9001"]["point_total"] == 75


def test_single_event_bonus_includes_rookie_bonus(setup_full_event) -> None:
    setup_full_event("2025mndu")

    event_details = none_throws(EventDetails.get_by_id("2025mndu"))
    regional_pool_points = none_throws(event_details.regional_champs_pool_points)
    regional_pool_points["points"]["frc9002"] = TeamAtEventDistrictPoints(
        alliance_points=10,
        award_points=0,
        elim_points=0,
        qual_points=15,
        total=25,
    )
    event_details.regional_champs_pool_points = regional_pool_points
    event_details.put()

    event = none_throws(Event.get_by_id("2025mndu"))
    event.prep_details()

    rookie_single_event = Team(
        id="frc9002",
        team_number=9002,
        rookie_year=2025,
    )
    rookie_single_event.put()

    rankings = RegionalChampsPoolHelper.calculate_rankings(
        [event], [rookie_single_event], 2025, None
    )

    # E1 includes rookie bonus for regional events: 25 + 10
    # E2 = round(0.6 * E1) + 14 = round(0.6 * 35) + 14 = 35
    assert rankings["frc9002"]["rookie_bonus"] == 10
    assert rankings["frc9002"]["single_event_bonus"] == 35
    assert rankings["frc9002"]["point_total"] == 70
