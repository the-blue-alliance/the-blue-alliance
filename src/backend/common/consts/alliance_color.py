import enum
from typing import List, Union

from typing_extensions import Literal


@enum.unique
class AllianceColor(str, enum.Enum):
    RED = "red"
    BLUE = "blue"


TMatchWinner = Union[AllianceColor, Literal[""]]


ALLIANCE_COLORS: List[AllianceColor] = list([c.value for c in AllianceColor])
