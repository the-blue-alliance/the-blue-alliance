from backend.api.handlers.helpers.nexus_info_converter import (
    event_queue_status_to_api,
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
