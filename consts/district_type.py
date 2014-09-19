class DistrictType(object):
    """
    Constants for what district an Event is a part of
    """
    # Event is not a district event
    NO_DISTRICT = 0

    MICHIGAN = 1
    MID_ATLANTIC = 2
    NEW_ENGLAND = 3
    PACIFIC_NORTHWEST = 4
    INDIANA = 5

    # Used for rendering
    type_names = {
        NO_DISTRICT: None,
        MICHIGAN: 'Michigan',
        MID_ATLANTIC: 'Mid Atlantic',
        NEW_ENGLAND: 'New England',
        PACIFIC_NORTHWEST: 'Pacific Northwest',
        INDIANA: 'Indiana',
    }

    type_abbrevs = {
        NO_DISTRICT: None,
        MICHIGAN: 'fim',
        MID_ATLANTIC: 'mar',
        NEW_ENGLAND: 'ne',
        PACIFIC_NORTHWEST: 'pnw',
        INDIANA: 'in',
    }

    # Names used on the FIRST website
    names = {
        'FIRST in Michigan': MICHIGAN,
        'Mid-Atlantic Robotics': MID_ATLANTIC,
        'New England': NEW_ENGLAND,
        'Pacific Northwest': PACIFIC_NORTHWEST,
        'Indiana': INDIANA,
    }

    abbrevs = {
        'fim': MICHIGAN,
        'mar': MID_ATLANTIC,
        'ne': NEW_ENGLAND,
        'pnw': PACIFIC_NORTHWEST,
        'in': INDIANA,
    }
