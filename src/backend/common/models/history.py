from typing import TypedDict

from backend.common.models.award import Award
from backend.common.models.event import Event


class History(TypedDict):
    events: list[Event]
    awards: list[Award]
