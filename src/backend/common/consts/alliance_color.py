import enum
from typing import List


@enum.unique
class AllianceColor(enum.Enum):
    RED = "red"
    BLUE = "blue"


ALLIANCE_COLORS: List[AllianceColor] = list(AllianceColor)
