import json
from datetime import datetime
from typing import cast, List, Optional

import pytest
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.frc_api.types import ScheduleListModelV31, ScheduleTeamModelV2
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_match_parser import (
    FMSAPIPracticeScheduleParser,
)


@pytest.fixture(autouse=True)
def event(ndb_stub) -> Event:
    event = Event(
        id="2026nysu",
        event_type_enum=EventType.REGIONAL,
        event_short="nysu",
        year=2026,
        start_date=datetime(2026, 3, 19),
        end_date=datetime(2026, 3, 21),
        official=True,
        timezone_id="America/New_York",
    )
    event.put()
    return event


def _schedule(red2: Optional[int], start_time: Optional[str]) -> ScheduleListModelV31:
    stations = [("Red1", 1111), ("Red2", red2), ("Red3", 3333)] + [
        ("Blue1", 4444),
        ("Blue2", 5555),
        ("Blue3", 6666),
    ]
    return {
        "Schedule": [
            {
                "playoffLevel": None,
                "description": "Practice 1",
                "startTime": start_time,
                "matchNumber": 1,
                "field": "Primary",
                "tournamentLevel": "Practice",
                "teams": [
                    ScheduleTeamModelV2(
                        teamNumber=number, station=station, surrogate=False
                    )
                    for station, number in stations
                ],
            }
        ]
    }


def _parse(response: ScheduleListModelV31) -> List[Match]:
    return FMSAPIPracticeScheduleParser(2026, "nysu").parse(response)


def test_parse_practice_schedule(test_data_importer) -> None:
    path = test_data_importer._get_path(
        __file__, "data/2026nysu_practice_schedule.json"
    )
    with open(path, "r") as f:
        matches = _parse(json.load(f))

    assert len(matches) == 32
    assert all(m.comp_level == CompLevel.PM for m in matches)
    assert all(not m.has_been_played for m in matches)

    match = matches[0]
    assert match.key.id() == "2026nysu_pm1"
    assert match.set_number == 1
    assert match.match_number == 1
    assert match.time == datetime(2026, 3, 19, 16, 0)
    assert match.alliances[AllianceColor.RED]["teams"] == [
        "frc6401",
        "frc10213",
        "frc2053",
    ]
    assert match.alliances[AllianceColor.BLUE]["teams"] == [
        "frc3419",
        "frc9636",
        "frc333",
    ]
    assert match.team_key_names == [
        "frc6401",
        "frc10213",
        "frc2053",
        "frc3419",
        "frc9636",
        "frc333",
    ]


def test_parse_missing_schedule() -> None:
    assert _parse({"Schedule": None}) == []
    assert _parse(cast(ScheduleListModelV31, {})) == []


def test_parse_skips_unscheduled_match() -> None:
    assert _parse(_schedule(2222, None)) == []


def test_parse_keeps_match_with_open_station() -> None:
    [match] = _parse(_schedule(None, "2026-03-19T12:00:00"))

    assert match.alliances[AllianceColor.RED]["teams"] == ["frc1111", "frc3333"]
    assert len(match.team_key_names) == 5


def test_substitute_replaces_scheduled_team(taskqueue_stub) -> None:
    MatchManipulator.createOrUpdate(
        _parse(_schedule(1234, "2026-03-19T12:00:00")), run_post_update_hook=False
    )
    MatchManipulator.createOrUpdate(
        _parse(_schedule(9876, "2026-03-19T12:00:00")), run_post_update_hook=False
    )

    match = none_throws(Match.get_by_id("2026nysu_pm1"))
    assert match.alliances[AllianceColor.RED]["teams"] == [
        "frc1111",
        "frc9876",
        "frc3333",
    ]
    assert "frc1234" not in match.team_key_names
    assert "frc9876" in match.team_key_names
