from typing import Dict, TypedDict

from backend.common.models.keys import TeamKey


class EventMatchstats(TypedDict):
    oprs: Dict[TeamKey, float]
    dprs: Dict[TeamKey, float]
    ccwms: Dict[TeamKey, float]
