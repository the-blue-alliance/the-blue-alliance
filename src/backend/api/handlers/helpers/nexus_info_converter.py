from typing import Dict, NewType, Optional

from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.nexus_api.types import PitMap, Pits

NexusInfoDict = NewType("NexusInfoDict", Dict)


def nexus_info_to_api(
    queue_status: Optional[EventQueueStatus], pit_map: Optional[PitMap]
) -> Optional[NexusInfoDict]:
    if not queue_status and not pit_map:
        return None

    info = (
        event_queue_status_to_api(queue_status)
        if queue_status
        else NexusInfoDict({"data_as_of_ms": None, "now_queueing": None, "matches": {}})
    )
    info["pit_map"] = _pit_map_to_api(pit_map) if pit_map else None
    return info


def _pit_map_to_api(pit_map: PitMap) -> Dict:
    return {
        "size": pit_map.get("size"),
        "pits": {
            pit_id: _pit_to_api(pit)
            for pit_id, pit in (pit_map.get("pits") or {}).items()
        },
        "areas": pit_map.get("areas") or {},
        "labels": pit_map.get("labels") or {},
        "arrows": pit_map.get("arrows") or {},
        "walls": pit_map.get("walls") or {},
    }


def _pit_to_api(pit: Pits) -> Dict:
    team = (pit.get("team") or "").strip().lower()
    return {
        **{field: value for field, value in pit.items() if field != "team"},
        "team_key": f"frc{team}" if team else None,
    }


def event_queue_status_to_api(queue_status: EventQueueStatus) -> NexusInfoDict:
    """
    Converts an EventQueueStatus (as fetched from Nexus and cached by tasks_io)
    into a JSON-serializable dict for the API, rendering match status as its
    human-readable string instead of the raw NexusMatchStatus int enum.
    """
    now_queueing = queue_status["now_queueing"]

    matches = {
        match_key: {
            "label": match["label"],
            "status": NexusMatchStatus(match["status"]).to_string(),
            "played": match["played"],
            "times": match["times"],
        }
        for match_key, match in queue_status["matches"].items()
    }

    return NexusInfoDict(
        {
            "data_as_of_ms": queue_status["data_as_of_ms"],
            "now_queueing": now_queueing,
            "matches": matches,
        }
    )
