from typing import Dict, NewType

from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.models.event_queue_status import EventQueueStatus

NexusInfoDict = NewType("NexusInfoDict", Dict)


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
