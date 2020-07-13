import enum


@enum.unique
class AuthType(enum.IntEnum):
    """
    An auth type defines what write privileges an authenticated agent has.
    """

    # Write Types
    EVENT_DATA = 0  # DEPRECATED - USE FINER PERMISSIONS INSTEAD
    MATCH_VIDEO = 1
    EVENT_TEAMS = 2
    EVENT_MATCHES = 3
    EVENT_RANKINGS = 4
    EVENT_ALLIANCES = 5
    EVENT_AWARDS = 6
    EVENT_INFO = 7
    ZEBRA_MOTIONWORKS = 8

    # Read Type
    READ_API = 1000


WRITE_TYPE_NAMES = {
    # AuthType.EVENT_DATA: "event data",  # DEPRECATED
    AuthType.MATCH_VIDEO: "match video",
    AuthType.EVENT_TEAMS: "event teams",
    AuthType.EVENT_MATCHES: "event matches",
    AuthType.EVENT_RANKINGS: "event rankings",
    AuthType.EVENT_ALLIANCES: "event alliances",
    AuthType.EVENT_AWARDS: "event awards",
    AuthType.EVENT_INFO: "event info",
    AuthType.ZEBRA_MOTIONWORKS: "zebra motionworks",
}
