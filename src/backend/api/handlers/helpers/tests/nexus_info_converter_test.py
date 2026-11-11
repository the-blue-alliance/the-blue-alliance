from typing import Optional

import pytest

from backend.api.handlers.helpers.nexus_info_converter import (
    event_queue_status_to_api,
    nexus_info_to_api,
)
from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.models.event_queue_status import EventQueueStatus


def test_event_queue_status_to_api() -> None:
    queue_status = EventQueueStatus(
        data_as_of_ms=1721000000000,
        now_queueing={
            "match_key": "2024casj_qm5",
            "match_name": "Qualification 5",
        },
        matches={
            "2024casj_qm5": {
                "label": "Qualification 5",
                "status": NexusMatchStatus.NOW_QUEUING,
                "played": False,
                "times": {
                    "estimated_queue_time_ms": 1721000060000,
                    "estimated_start_time_ms": 1721000300000,
                },
            },
            "2024casj_qm4": {
                "label": "Qualification 4",
                "status": NexusMatchStatus.ON_FIELD,
                "played": False,
                "times": {
                    "estimated_queue_time_ms": None,
                    "estimated_start_time_ms": None,
                },
            },
        },
    )

    result = event_queue_status_to_api(queue_status)

    assert result["data_as_of_ms"] == 1721000000000
    assert result["now_queueing"] == {
        "match_key": "2024casj_qm5",
        "match_name": "Qualification 5",
    }
    assert result["matches"]["2024casj_qm5"] == {
        "label": "Qualification 5",
        "status": "Now queuing",
        "played": False,
        "times": {
            "estimated_queue_time_ms": 1721000060000,
            "estimated_start_time_ms": 1721000300000,
        },
    }
    assert result["matches"]["2024casj_qm4"]["status"] == "On field"


def test_event_queue_status_to_api_no_now_queueing() -> None:
    queue_status = EventQueueStatus(
        data_as_of_ms=1721000000000,
        now_queueing=None,
        matches={},
    )

    result = event_queue_status_to_api(queue_status)

    assert result["now_queueing"] is None
    assert result["matches"] == {}


def test_nexus_info_to_api_none_without_data() -> None:
    assert nexus_info_to_api(None, None) is None


def test_nexus_info_to_api_none_with_empty_pit_map() -> None:
    assert nexus_info_to_api(None, {}) is None


def test_nexus_info_to_api_queue_status_only_has_null_pit_map() -> None:
    queue_status = EventQueueStatus(
        data_as_of_ms=1721000000000,
        now_queueing=None,
        matches={},
    )

    result = nexus_info_to_api(queue_status, None)

    assert result is not None
    assert result["pit_map"] is None


def test_nexus_info_to_api_pit_map_only_has_empty_queue_fields() -> None:
    result = nexus_info_to_api(None, {"size": {"x": 100, "y": 50}, "pits": {}})

    assert result is not None
    assert (result["data_as_of_ms"], result["now_queueing"], result["matches"]) == (
        None,
        None,
        {},
    )


def test_nexus_info_to_api_pit_map() -> None:
    result = nexus_info_to_api(
        None,
        {
            "size": {"x": 100, "y": 50},
            "pits": {
                "A1": {
                    "position": {"x": 10, "y": 20},
                    "size": {"x": 8, "y": 8},
                    "angle": 90,
                    "team": "1678",
                },
            },
            "areas": {
                "area1": {
                    "position": {"x": 0, "y": 0},
                    "size": {"x": 30, "y": 30},
                    "label": "Inspection",
                },
            },
            "labels": None,
            "arrows": {
                "arrow1": {
                    "position": {"x": 5, "y": 5},
                    "size": {"x": 10, "y": 2},
                    "type": "double",
                },
            },
            "walls": None,
        },
    )

    assert result is not None
    assert result["pit_map"] == {
        "size": {"x": 100, "y": 50},
        "pits": {
            "A1": {
                "position": {"x": 10, "y": 20},
                "size": {"x": 8, "y": 8},
                "angle": 90,
                "team_key": "frc1678",
            },
        },
        "areas": {
            "area1": {
                "position": {"x": 0, "y": 0},
                "size": {"x": 30, "y": 30},
                "label": "Inspection",
            },
        },
        "labels": {},
        "arrows": {
            "arrow1": {
                "position": {"x": 5, "y": 5},
                "size": {"x": 10, "y": 2},
                "type": "double",
            },
        },
        "walls": {},
    }


@pytest.mark.parametrize(
    "team, expected_team_key",
    [
        ("1678", "frc1678"),
        (" 1678B ", "frc1678b"),
        ("", None),
        (None, None),
    ],
)
def test_nexus_info_to_api_pit_team_key(
    team: Optional[str], expected_team_key: Optional[str]
) -> None:
    result = nexus_info_to_api(
        None,
        {"size": {"x": 100, "y": 50}, "pits": {"A1": {"team": team}}},
    )

    assert result is not None
    assert result["pit_map"]["pits"]["A1"]["team_key"] == expected_team_key
