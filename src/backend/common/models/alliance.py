import enum
from typing import List

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


@enum.unique
class AllianceColor(enum.Enum):
    RED = "red"
    BLUE = "blue"


ALLIANCE_COLORS: List[AllianceColor] = list(AllianceColor)


class EventAlliance(TypedDict):
    picks: List[TeamKey]
    declines: List[TeamKey]


class MatchAlliance(TypedDict):
    teams: List[TeamKey]
    score: int
    surrogates: List[TeamKey]
    dqs: List[TeamKey]
