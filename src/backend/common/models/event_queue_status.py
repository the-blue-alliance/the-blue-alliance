from typing import TypedDict

from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.models.keys import MatchKey


class NexusCurrentlyQueueing(TypedDict):
    match_key: MatchKey
    match_name: str


class NexusMatchTiming(TypedDict):
    estimated_queue_time_ms: int | None
    estimated_start_time_ms: int | None


class NexusMatch(TypedDict):
    label: str
    status: NexusMatchStatus
    played: bool
    times: NexusMatchTiming


class EventQueueStatus(TypedDict):
    data_as_of_ms: int
    now_queueing: NexusCurrentlyQueueing | None
    matches: dict[MatchKey, NexusMatch]
