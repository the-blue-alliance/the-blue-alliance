import time
from database.dict_converters.converter_base import ConverterBase


class MatchConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 0,
    }

    @classmethod
    def convert(cls, matches, dict_version):
        CONVERTERS = {
            3: cls.matchesConverter_v3,
        }
        converted_matches = CONVERTERS[dict_version](cls._listify(matches))
        return cls._delistify(converted_matches)

    @classmethod
    def matchesConverter_v3(cls, matches):
        return map(cls.matchConverter_v3, matches)

    @classmethod
    def matchConverter_v3(cls, match):
        match_dict = {
            'key': match.key.id(),
            'event_key': match.event.id(),
            'comp_level': match.comp_level,
            'set_number': match.set_number,
            'match_number': match.match_number,
            'alliances': match.alliances,
            'winning_alliance': match.winning_alliance,
            'score_breakdown': match.score_breakdown,
            'videos': match.videos,
        }
        if match.time is not None:
            match_dict['time'] = int(time.mktime(match.time.timetuple()))
        else:
            match_dict['time'] = None
        if match.actual_time is not None:
            match_dict['actual_time'] = int(time.mktime(match.actual_time.timetuple()))
        else:
            match_dict['actual_time'] = None

        return match_dict
