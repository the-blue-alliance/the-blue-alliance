import json

import pytest
from pyre_extensions import none_throws

from backend.common.helpers.district_helper import (
    DistrictHelper,
    DistrictRankingTeamTotal,
    DistrictRankingTiebreakers,
    TeamAtEventDistrictPoints,
)
from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.models.team import Team


@pytest.mark.parametrize(
    "event_key",
    [
        "2024nytr",  # A 2024 event with a backup team
        "2024necmp",  # A 2024 event where one alliance wins no matches
        "2024test",  # A 2024 event with backup robot wins in the final
        "2023onlon",  # A 2023 event with backup robot wins in the final
        "2023mijac",  # A 2023 event
        "2023njfla",  # A 2023 event with backup team district points (wins and losses)
        "2023micmp",  # A double elimination DCMP with four divisions
        "2022on305",  # A 2022 single day event
        "2019nyny",  # A regular event
        "2015nyny",  # 2015 is special (average score ranking)
        "2018necmp",  # DCMP has 3x multiplier
        "2019micmp",  # A DCMP with divisions
        "2019micmp3",  # A DCMP Division
        "2015micmp",  # Special case because octofinals
        "2012pah",  # Pre-2014 accounted awards differently, used WLT for quals
    ],
)
def test_calc_event_points(
    event_key, ndb_stub, setup_full_event, test_data_importer
) -> None:
    setup_full_event(event_key)

    event = Event.get_by_id(event_key)
    assert event is not None
    event_points = DistrictHelper.calculate_event_points(event)

    with open(
        test_data_importer._get_path(
            __file__, f"data/{event_key}_district_points.json"
        ),
        "r",
    ) as f:
        expected_event_points = json.load(f)

    assert event_points == expected_event_points


def test_calculate_multi_event_rankings_all_teams_filtered(setup_full_event) -> None:
    setup_full_event("2019nyny")
    setup_full_event("2019micmp3")
    setup_full_event("2019micmp")

    events = [
        none_throws(Event.get_by_id("2019nyny")),
        none_throws(Event.get_by_id("2019micmp3")),
        none_throws(Event.get_by_id("2019micmp")),
    ]

    rankings = DistrictHelper.calculate_rankings(events, [], 2019)
    assert rankings == {}


def test_calculate_multi_event_rankings(setup_full_event) -> None:
    setup_full_event("2019nyny")
    setup_full_event("2019micmp3")
    setup_full_event("2019micmp")

    events = [
        none_throws(Event.get_by_id("2019nyny")),
        none_throws(Event.get_by_id("2019micmp3")),
        none_throws(Event.get_by_id("2019micmp")),
    ]
    teams = [
        none_throws(Team.get_by_id("frc694")),
        none_throws(Team.get_by_id("frc4362")),
    ]

    rankings = DistrictHelper.calculate_rankings(events, teams, 2019)
    assert len(rankings) == 2  # should match the two teams we passed
    assert rankings["frc694"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=5,
                    elim_points=30,
                    qual_points=19,
                    total=70,
                ),
            )
        ],
        point_total=70,
        qual_scores=[85, 71, 69],
        rookie_bonus=0,
        other_bonus=0,
        tiebreakers=DistrictRankingTiebreakers(*[30, 30, 16, 16, 19]),
    )
    assert rankings["frc4362"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[1],
                TeamAtEventDistrictPoints(
                    alliance_points=42,
                    award_points=15,
                    elim_points=90,
                    qual_points=60,
                    total=207,
                ),
            ),
            (
                events[2],
                TeamAtEventDistrictPoints(
                    alliance_points=0,
                    award_points=0,
                    elim_points=60,
                    qual_points=0,
                    total=60,
                ),
            ),
        ],
        point_total=267,
        qual_scores=[104, 97, 93],
        rookie_bonus=0,
        other_bonus=0,
        tiebreakers=DistrictRankingTiebreakers(*[150, 90, 42, 42, 60]),
    )


def test_2022_back_to_back_single_day_bonus(setup_full_event) -> None:
    setup_full_event("2022on305")
    setup_full_event("2022on306")

    events = [
        none_throws(Event.get_by_id("2022on305")),
        none_throws(Event.get_by_id("2022on306")),
    ]
    teams = [
        none_throws(Team.get_by_id("frc2200")),
        none_throws(Team.get_by_id("frc610")),
        none_throws(Team.get_by_id("frc1241")),
    ]

    rankings = DistrictHelper.calculate_rankings(events, teams, 2022)
    assert len(rankings) == 3
    assert rankings["frc2200"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=0,
                    elim_points=20,
                    qual_points=22,
                    total=58,
                ),
            ),
            (
                events[1],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=5,
                    elim_points=20,
                    qual_points=22,
                    total=63,
                ),
            ),
        ],
        point_total=123,
        qual_scores=[93, 82, 82],
        rookie_bonus=0,
        other_bonus=2,
        tiebreakers=DistrictRankingTiebreakers(*[40, 20, 32, 16, 44]),
    )
    assert rankings["frc610"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=5,
                    elim_points=20,
                    qual_points=18,
                    total=59,
                ),
            )
        ],
        point_total=59,
        qual_scores=[52, 41, 40],
        rookie_bonus=0,
        other_bonus=0,
        tiebreakers=DistrictRankingTiebreakers(*[20, 20, 16, 16, 18]),
    )
    assert rankings["frc1241"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[1],
                TeamAtEventDistrictPoints(
                    alliance_points=14,
                    award_points=5,
                    elim_points=10,
                    qual_points=12,
                    total=41,
                ),
            )
        ],
        point_total=41,
        qual_scores=[67, 56, 45],
        rookie_bonus=0,
        other_bonus=0,
        tiebreakers=DistrictRankingTiebreakers(*[10, 10, 14, 14, 12]),
    )


@pytest.mark.parametrize(
    "year,rookie_year,bonus",
    [
        (2020, 2020, 10),
        (2020, 2019, 5),
        (2022, 2022, 10),
        (2022, 2021, 10),
        (2022, 2020, 5),
        (2022, 2019, 0),
        (2023, 2023, 10),
        (2023, 2022, 5),
        (2023, 2021, 5),
        (2023, 2020, 0),
        (2023, 2019, 0),
    ],
)
def test_pandemic_rookie_edge_cases(year: Year, rookie_year: Year, bonus: int) -> None:
    assert DistrictHelper._get_rookie_bonus(year, rookie_year) == bonus
