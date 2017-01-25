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
            'alliances': event_details.alliance_selections if event_details else None,
            'district_points': event_details.district_points if event_details else None,
            'rankings': event_details.renderable_rankings if event_details else None,
            'stats': event_details.matchstats if event_details else None,
        }

        return event_details_dict
