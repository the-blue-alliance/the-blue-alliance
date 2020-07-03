from typing import List

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


class _EventAllianceOptional(TypedDict, total=False):
    declines: List[TeamKey]


class EventAlliance(_EventAllianceOptional, total=True):
    picks: List[TeamKey]


class _MatchAllianceOptional(TypedDict, total=False):
    surrogates: List[TeamKey]
    dqs: List[TeamKey]


class MatchAlliance(_MatchAllianceOptional, total=True):
    teams: List[TeamKey]
    score: int
