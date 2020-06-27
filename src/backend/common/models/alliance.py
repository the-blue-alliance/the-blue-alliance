from typing import List

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey


class Alliance(TypedDict):
    picks: List[TeamKey]
    declines: List[TeamKey]
