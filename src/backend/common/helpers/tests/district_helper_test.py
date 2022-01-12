import json

import pytest
from pyre_extensions import none_throws

from backend.common.helpers.district_helper import DistrictHelper
from backend.common.models.event import Event
from backend.common.models.team import Team


@pytest.mark.parametrize(
    "event_key",
    [
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
    assert rankings["frc694"] == {
        "event_points": [
            (
                events[0],
                {
                    "alliance_points": 16,
                    "award_points": 5,
                    "elim_points": 30,
                    "qual_points": 19,
                    "total": 70,
                },
            )
        ],
        "point_total": 70,
        "qual_scores": [85, 71, 69],
        "rookie_bonus": 0,
        "tiebreakers": [30, 30, 16, 19, 0],
    }
    assert rankings["frc4362"] == {
        "event_points": [
            (
                events[1],
                {
                    "alliance_points": 42,
                    "award_points": 15,
                    "elim_points": 90,
                    "qual_points": 60,
                    "total": 207,
                },
            ),
            (
                events[2],
                {
                    "alliance_points": 0,
                    "award_points": 0,
                    "elim_points": 60,
                    "qual_points": 0,
                    "total": 60,
                },
            ),
        ],
        "point_total": 267,
        "qual_scores": [104, 97, 93],
        "rookie_bonus": 0,
        "tiebreakers": [150, 90, 42, 60, 0],
    }
