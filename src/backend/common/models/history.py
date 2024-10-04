from typing import List, TypedDict

from backend.common.models.award import Award
from backend.common.models.event import Event


class History(TypedDict):
    events: List[Event]
    awards: List[Award]
