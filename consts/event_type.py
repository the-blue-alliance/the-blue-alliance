class EventType(object):
    REGIONAL = 0
    DISTRICT = 1
    DISTRICT_CMP = 2
    CMP_DIVISION = 3
    CMP_FINALS = 4
    DISTRICT_CMP_DIVISION = 5
    FOC = 6

    OFFSEASON = 99
    PRESEASON = 100
    UNLABLED = -1

    type_names = {
        REGIONAL: 'Regional',
        DISTRICT: 'District',
        DISTRICT_CMP_DIVISION: 'District Championship Division',
        DISTRICT_CMP: 'District Championship',
        CMP_DIVISION: 'Championship Division',
        CMP_FINALS: 'Championship Finals',
        FOC: 'Festival of Champions',
        OFFSEASON: 'Offseason',
        PRESEASON: 'Preseason',
        UNLABLED: '--',
    }

    short_type_names = {
        REGIONAL: 'Regional',
        DISTRICT: 'District',
        DISTRICT_CMP_DIVISION: 'District Championship Division',
        DISTRICT_CMP: 'District Championship',
        CMP_DIVISION: 'Division',
        CMP_FINALS: 'Championship',
        FOC: 'FoC',
        OFFSEASON: 'Offseason',
        PRESEASON: 'Preseason',
        UNLABLED: '--',
    }

    DISTRICT_EVENT_TYPES = {
        DISTRICT,
        DISTRICT_CMP_DIVISION,
        DISTRICT_CMP,
    }

    NON_CMP_EVENT_TYPES = {
        REGIONAL,
        DISTRICT,
        DISTRICT_CMP_DIVISION,
        DISTRICT_CMP,
    }

    CMP_EVENT_TYPES = {
        CMP_DIVISION,
        CMP_FINALS,
    }

    SEASON_EVENT_TYPES = {
        REGIONAL,
        DISTRICT,
        DISTRICT_CMP_DIVISION,
        DISTRICT_CMP,
        CMP_DIVISION,
        CMP_FINALS,
        FOC,
    }
