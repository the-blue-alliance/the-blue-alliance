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
    CHESAPEAKE = 6
    NORTH_CAROLINA = 7
    GEORGIA = 8
    ONTARIO = 9
    ISRAEL = 10

    # Used for rendering
    type_names = {
        NO_DISTRICT: None,
        MICHIGAN: 'Michigan',
        MID_ATLANTIC: 'Mid Atlantic',
        NEW_ENGLAND: 'New England',
        PACIFIC_NORTHWEST: 'Pacific Northwest',
        INDIANA: 'Indiana',
        CHESAPEAKE: 'Chesapeake',
        NORTH_CAROLINA: 'North Carolina',
        GEORGIA: 'Georgia',
        ONTARIO: 'Ontario',
        ISRAEL: 'Israel',
    }

    # make sure abbreviations stay all lower case
    type_abbrevs = {
        NO_DISTRICT: None,
        MICHIGAN: 'fim',
        MID_ATLANTIC: 'mar',
        NEW_ENGLAND: 'ne',
        PACIFIC_NORTHWEST: 'pnw',
        INDIANA: 'in',
        CHESAPEAKE: 'chs',
        NORTH_CAROLINA: 'nc',
        GEORGIA: 'pch',
        ONTARIO: 'ont',
        ISRAEL: 'isr',
    }

    # Names used on the FIRST website & FRC API
    names = {
        'FIRST in Michigan': MICHIGAN,
        'Mid-Atlantic Robotics': MID_ATLANTIC,
        'New England': NEW_ENGLAND,
        'Pacific Northwest': PACIFIC_NORTHWEST,
        'IndianaFIRST': INDIANA,
        'FIRST Chesapeake': CHESAPEAKE,
        'North Carolina': NORTH_CAROLINA,
        'Georgia': GEORGIA,
        'FIRST Ontario': ONTARIO,
        'Israel': ISRAEL,
    }

    # Names used by FIRST ElasticSearch
    elasticsearch_names = {
        'Michigan': MICHIGAN,
        'Mid-Atlantic': MID_ATLANTIC,
        'New England': NEW_ENGLAND,
        'NE FIRST': NEW_ENGLAND,
        'Pacific Northwest': PACIFIC_NORTHWEST,
        'Indiana': INDIANA,
        'Chesapeake': CHESAPEAKE,
        'NC FIRST': NORTH_CAROLINA,
        'FIRST North Carolina': NORTH_CAROLINA,  # 2017 uses a different name
        'Peachtree': GEORGIA,
        'FIRST Ontario': ONTARIO,
        'FIRST Israel': ISRAEL,
    }

    # make sure abbreviations stay all lower case
    abbrevs = {
        'fim': MICHIGAN,
        'mar': MID_ATLANTIC,
        'ne': NEW_ENGLAND,
        'pnw': PACIFIC_NORTHWEST,
        'in': INDIANA,
        'chs': CHESAPEAKE,
        'nc': NORTH_CAROLINA,
        'pch': GEORGIA,
        'ont': ONTARIO,
        'isr': ISRAEL,
    }
