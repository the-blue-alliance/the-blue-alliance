import enum

from typing_extensions import Literal

from backend.common.consts.string_enum import StrEnum


@enum.unique
class AllianceColor(StrEnum):
    RED = "red"
    BLUE = "blue"


OPPONENT: dict[AllianceColor, AllianceColor] = {
    AllianceColor.RED: AllianceColor.BLUE,
    AllianceColor.BLUE: AllianceColor.RED,
}


TMatchWinner = AllianceColor | Literal[""]


ALLIANCE_COLORS: list[str] = [c.value for c in AllianceColor]
