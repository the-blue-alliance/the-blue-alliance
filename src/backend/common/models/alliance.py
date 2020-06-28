from typing import List

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


class EventAlliance(TypedDict):
    picks: List[TeamKey]
    declines: List[TeamKey]


class MatchAlliance(TypedDict):
    teams: List[TeamKey]
    score: int
    surrogates: List[TeamKey]
    dqs: List[TeamKey]
