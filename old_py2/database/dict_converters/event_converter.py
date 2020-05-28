from consts.playoff_type import PlayoffType
from database.dict_converters.converter_base import ConverterBase
from database.dict_converters.district_converter import DistrictConverter


class EventConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 6,
    }

    @classmethod
    def _convert(cls, events, dict_version):
        CONVERTERS = {
            3: cls.eventsConverter_v3,
        }
        return CONVERTERS[dict_version](events)

    @classmethod
    def eventsConverter_v3(cls, events):
        events = map(cls.eventConverter_v3, events)
        return events

    @classmethod
    def eventConverter_v3(cls, event):
        district_future = event.district_key.get_async() if event.district_key else None
        event_dict = {
            'key': event.key.id(),
            'name': event.name,
            'short_name': event.short_name,
            'event_code': event.event_short,
            'event_type': event.event_type_enum,
            'event_type_string': event.event_type_str,
            'parent_event_key': event.parent_event.id() if event.parent_event else None,
            'playoff_type': event.playoff_type,
            'playoff_type_string': PlayoffType.type_names.get(event.playoff_type),
            'district': DistrictConverter.convert(district_future.get_result(), 3) if district_future else None,
            'division_keys': [key.id() for key in event.divisions],
            'first_event_id': event.first_eid,
            'first_event_code': event.first_api_code if event.official else None,
            'year': event.year,
            'timezone': event.timezone_id,
            'week': event.week,
            'website': event.website,
        }
        event_dict.update(cls.constructLocation_v3(event))

        if event.start_date:
            event_dict['start_date'] = event.start_date.date().isoformat()
        else:
            event_dict['start_date'] = None
        if event.end_date:
            event_dict['end_date'] = event.end_date.date().isoformat()
        else:
            event_dict['end_date'] = None

        if event.webcast:
            event_dict['webcasts'] = event.webcast
        else:
            event_dict['webcasts'] = []

        return event_dict
