class AuthType(object):
    """
    An auth type defines what write privileges an authenticated agent has.
    """
    MATCH_VIDEO = 0
    EVENT_TEAMS = 1
    EVENT_MATCHES = 2
    EVENT_RANKINGS = 3
    EVENT_ALLIANCES = 4
    EVENT_AWARDS = 5

    type_names = {
        MATCH_VIDEO: "match video",
        EVENT_TEAMS: "event teams",
        EVENT_MATCHES: "event matches",
        EVENT_RANKINGS: "event rankings",
        EVENT_ALLIANCES: "event alliances",
        EVENT_AWARDS: "event awrads"
    }
