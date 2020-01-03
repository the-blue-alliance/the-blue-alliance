class AuthType(object):
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

    write_type_names = {
        # EVENT_DATA: "event data",  # DEPRECATED
        MATCH_VIDEO: "match video",
        EVENT_TEAMS: "event teams",
        EVENT_MATCHES: "event matches",
        EVENT_RANKINGS: "event rankings",
        EVENT_ALLIANCES: "event alliances",
        EVENT_AWARDS: "event awards",
        EVENT_INFO: "event info",
        ZEBRA_MOTIONWORKS: "zebra motionworks",
    }
