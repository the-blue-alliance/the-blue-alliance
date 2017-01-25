from database.dict_converters.converter_base import ConverterBase


class EventDetailsConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 0,
    }

    @classmethod
    def convert(cls, event_details, dict_version):
        CONVERTERS = {
            3: cls.eventDetailsConverter_v3,
        }
        return CONVERTERS[dict_version](event_details)

    @classmethod
    def eventDetailsConverter_v3(cls, event_details):
        event_details_dict = {
            'alliances': event_details.alliance_selections,
            'district_points': event_details.district_points,
            'rankings': event_details.renderable_rankings,
            'stats': event_details.matchstats,
        }

        return event_details_dict
