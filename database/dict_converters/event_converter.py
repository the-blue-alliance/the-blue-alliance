from database.dict_converters.converter_base import ConverterBase


class EventConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 0,
    }

    @classmethod
    def convert(cls, events, dict_version):
        EVENT_CONVERTERS = {
            3: cls.eventsConverter_v3,
        }
        return EVENT_CONVERTERS[dict_version](events)

    @classmethod
    def eventsConverter_v3(cls, events):
        events = map(cls.eventConverter_v3, events)
        return events

    @classmethod
    def eventConverter_v3(cls, event):
        event_dict = {
            'key': event.key.id(),
            'name': event.name,
            'short_name': event.short_name,
            'event_code': event.event_short,
            'event_type': event.event_type_enum,
            'event_type_string': event.event_type_str,
            'district_type': event.event_district_enum,
            'district_type_string': event.event_district_str,
            'first_event_id': event.first_eid,
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
