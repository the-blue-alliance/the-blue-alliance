import logging


class ChampSplitHelper(object):
    """
    http://www.firstinspires.org/sites/default/files/uploads/championship/first-championship-maps-2017-2018.pdf
    """
    STL = 'St. Louis'
    HOU = 'Houston'
    DET = 'Detroit'

    YELLOW = {2017: HOU, 2018: HOU}
    BLUE = {2017: STL, 2018: DET}

    LOCATION_CHAMP_MAP = {
        'USA': {
            'Washington': HOU,
            'Oregon': HOU,
            'California': HOU,
            'Nevada': HOU,
            'Idaho': HOU,
            'Montana': HOU,
            'Wyoming': HOU,
            'Colorado': HOU,
            'Utah': HOU,
            'Arizona': HOU,
            'New Mexico': HOU,
            'Texas': HOU,
            'Oklahoma': HOU,
            'Arkansas': HOU,
            'Louisiana': HOU,
            'Mississippi': HOU,
            'Tennessee': HOU,
            'Alabama': HOU,
            'Georgia': HOU,
            'North Carolina': HOU,
            'South Carolina': HOU,
            'Florida': HOU,
            'Alaska': HOU,
            'Hawaii': HOU,
        },
        'Canada': {
            'Yukon': HOU,
            'Northwest Territories': HOU,
            'British Columbia': HOU,
            'Alberta': HOU,
            'Saskatchewan': HOU,
        },
        'Mexico': YELLOW,
        'China': YELLOW,
        'Brazil': YELLOW,
        'Ecuador': YELLOW,
        'Israel': YELLOW,
        'Australia': YELLOW,
        'Singapore': YELLOW,
        'Chile': YELLOW,
        'China': YELLOW,
        'Dominican Republic': YELLOW,
        'Philippines': YELLOW,
        'Turkey': YELLOW,
        'Mexico': YELLOW,
        'United Arab Emirates': YELLOW,
        'India': YELLOW,
        'Colombia': YELLOW,
        'Malaysia': YELLOW,
        'Kazakhstan': BLUE,
        'Germany': BLUE,
        'Spain': BLUE,
        'Netherlands': BLUE,
        'Denmark': BLUE,
        'Pakistan': BLUE,
        'Poland': BLUE,
        'United Kingdom': BLUE,
        'Japan': BLUE,
        'Taiwan': BLUE,
        'Bosnia-Herzegovina': BLUE,
        'Kingdom': BLUE,
        'Czech Republic': BLUE,
        'France': BLUE,
        'Switzerland': BLUE,
        'Vietnam': BLUE,
    }

    @classmethod
    def get_champ(cls, team):
        if team.country in cls.LOCATION_CHAMP_MAP:
            if team.country in {'USA', 'Canada'}:
                if team.state_prov in cls.LOCATION_CHAMP_MAP[team.country]:
                    champ = cls.LOCATION_CHAMP_MAP[team.country][team.state_prov]
                    return {2017: champ, 2018: champ}
                elif team.state_prov in {'Kansas', 'Missouri'}:
                    return {2017: cls.STL, 2018: cls.HOU}
                else:
                    # All other unlabled states and provinces in US and CA are STL/DET
                    return {2017: cls.STL, 2018: cls.DET}
            else:
                # Non US/CA other countries
                return cls.LOCATION_CHAMP_MAP[team.country]
        else:
            if team.country is not None:
                logging.warning("[champ_split_helper.py] Unknown country: {}".format(team.country))
            return None
