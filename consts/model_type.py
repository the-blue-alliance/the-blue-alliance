class ModelType(object):
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

    # Used for rendering
    type_names = {
        EVENT: 'Event',
        TEAM: 'Team',
        MATCH: 'Match',
        EVENT_TEAM: 'Event Team',
        DISTRICT: 'District',
        DISTRICT_TEAM: 'District Team',
        AWARD: 'Award',
        MEDIA: 'Media',
    }
