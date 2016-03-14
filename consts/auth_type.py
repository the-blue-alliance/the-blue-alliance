class AuthType(object):
    """
    An auth type defines what write privileges an authenticated agent has.
    """
    EVENT_DATA = 0  # DEPRECATED - USE FINER PERMISSIONS INSTEAD
    MATCH_VIDEO = 1
    EVENT_TEAMS = 2
    EVENT_MATCHES = 3
    EVENT_RANKINGS = 4
    EVENT_ALLIANCES = 5
    EVENT_AWARDS = 6

    type_names = {
        EVENT_DATA: "event data",
        MATCH_VIDEO: "match video",
        EVENT_TEAMS: "event teams",
        EVENT_MATCHES: "event matches",
        EVENT_RANKINGS: "event rankings",
        EVENT_ALLIANCES: "event alliances",
        EVENT_AWARDS: "event awrads"
    }
