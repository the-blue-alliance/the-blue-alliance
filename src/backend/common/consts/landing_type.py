import enum
from typing import Dict


@enum.unique
class LandingType(enum.IntEnum):
    # For choosing what the main landing page displays
    KICKOFF = 1
    BUILDSEASON = 2
    COMPETITIONSEASON = 3
    OFFSEASON = 4
    INSIGHTS = 5
    CHAMPS = 6


LANDING_TYPE_NAMES: Dict[LandingType, str] = {
    LandingType.KICKOFF: "Kickoff",
    LandingType.BUILDSEASON: "Build Season",
    LandingType.COMPETITIONSEASON: "Competition Season",
    LandingType.OFFSEASON: "Offseason",
    LandingType.INSIGHTS: "Insights",
    LandingType.CHAMPS: "Championship",
}
