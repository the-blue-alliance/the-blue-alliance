from typing import Dict

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


class EventMatchstats(TypedDict):
    oprs: Dict[TeamKey, float]
    dprs: Dict[TeamKey, float]
    ccwms: Dict[TeamKey, float]
    coprs: Dict[str, Dict[TeamKey, float]]
