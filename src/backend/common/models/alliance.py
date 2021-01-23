from typing import List

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


EventAllianceBackup = TypedDict("EventAllianceBackup", {"in": str, "out": str})


class _EventAllianceOptional(TypedDict, total=False):
    declines: List[TeamKey]
    name: str
    backup: EventAllianceBackup


class EventAlliance(_EventAllianceOptional, total=True):
    picks: List[TeamKey]


class _MatchAllianceOptional(TypedDict, total=False):
    surrogates: List[TeamKey]
    dqs: List[TeamKey]


class MatchAlliance(_MatchAllianceOptional, total=True):
    teams: List[TeamKey]
    score: int
