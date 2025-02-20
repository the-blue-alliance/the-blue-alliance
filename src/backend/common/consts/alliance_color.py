import enum
from typing import Dict, List, Union

from typing_extensions import Literal

from backend.common.consts.string_enum import StrEnum


@enum.unique
class AllianceColor(StrEnum):
    RED = "red"
    BLUE = "blue"


OPPONENT: Dict[AllianceColor, AllianceColor] = {
    AllianceColor.RED: AllianceColor.BLUE,
    AllianceColor.BLUE: AllianceColor.RED,
}


TMatchWinner = Union[AllianceColor, Literal[""]]


ALLIANCE_COLORS: List[AllianceColor] = list([c.value for c in AllianceColor])
