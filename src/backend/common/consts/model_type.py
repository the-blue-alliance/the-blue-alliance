import enum


@enum.unique
class ModelType(enum.IntEnum):
    """
    Enums for the different model types
    DO NOT CHANGE EXISTING ONES
    """

    EVENT = 0
    TEAM = 1
    MATCH = 2
    EVENT_TEAM = 3
    DISTRICT = 4
    DISTRICT_TEAM = 5
    AWARD = 6
    MEDIA = 7


TYPE_NAMES = {
    ModelType.EVENT: "Event",
    ModelType.TEAM: "Team",
    ModelType.MATCH: "Match",
    ModelType.EVENT_TEAM: "Event Team",
    ModelType.DISTRICT: "District",
    ModelType.DISTRICT_TEAM: "District Team",
    ModelType.AWARD: "Award",
    ModelType.MEDIA: "Media",
}
