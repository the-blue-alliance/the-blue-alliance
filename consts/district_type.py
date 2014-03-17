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

    # Names used on the FIRST website
    names = {
        'FIRST in Michigan': MICHIGAN,
        'Mid-Atlantic Robotics': MID_ATLANTIC,
        'New England': NEW_ENGLAND,
        'Pacific Northwest': PACIFIC_NORTHWEST,
    }
