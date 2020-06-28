from typing import List

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


class EventAlliance(TypedDict):
    picks: List[TeamKey]
    declines: List[TeamKey]


class _MatchAllianceOptional(TypedDict, total=False):
    surrogates: List[TeamKey]
    dqs: List[TeamKey]


class MatchAlliance(_MatchAllianceOptional, total=True):
    teams: List[TeamKey]
    score: int
