import json

import pytest
from pyre_extensions import none_throws

from backend.common.helpers.regional_champs_pool_helper import (
    DistrictRankingTeamTotal,
    RegionalChampsPoolHelper,
    RegionalChampsPoolTiebreakers,
)
from backend.common.models.event import Event
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
