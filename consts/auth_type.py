class AuthType(object):
    """
    An auth type defines what write privileges an authenticated agent has.
    """
    EVENT_DATA = 0
    MATCH_VIDEO = 1

    type_names = {
        EVENT_DATA: "event data",
        MATCH_VIDEO: "match video",
    }
