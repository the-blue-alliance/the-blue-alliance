from typing import List

from backend.common.models.event import Event

from backend.common.consts import playoff_type
from backend.common.queries.dict_converters.converter_base import ConverterBase


class EventConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 6,
    }

    def _convert_list(self, model_list: List[Event], version: int) -> List[dict]:
        CONVERTERS = {
            3: self.eventsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    def eventsConverter_v3(self, events: List[Event]) -> List[dict]:
        events = list(map(self.eventConverter_v3, events))
        return events

    def eventConverter_v3(self, event: Event) -> dict:
        # district_future = event.district_key.get_async() if event.district_key else None
        event_dict = {
            "key": event.key.id(),
            "name": event.name,
            "short_name": event.short_name,
            "event_code": event.event_short,
            "event_type": event.event_type_enum,
            "event_type_string": event.event_type_str,
            "parent_event_key": event.parent_event.id() if event.parent_event else None,
            "playoff_type": event.playoff_type,
            "playoff_type_string": playoff_type.TYPE_NAMES.get(event.playoff_type),
            # "district": DistrictConverter.convert(district_future.get_result(), 3)
            # if district_future
            # else None,
            "division_keys": [key.id() for key in event.divisions],
            "first_event_id": event.first_eid,
            "first_event_code": event.first_api_code if event.official else None,
            "year": event.year,
            "timezone": event.timezone_id,
            "week": event.week,
            "website": event.website,
        }
        event_dict.update(self.constructLocation_v3(event))

        if event.start_date:
            event_dict["start_date"] = event.start_date.date().isoformat()
        else:
            event_dict["start_date"] = None
        if event.end_date:
            event_dict["end_date"] = event.end_date.date().isoformat()
        else:
            event_dict["end_date"] = None

        if event.webcast:
            event_dict["webcasts"] = event.webcast
        else:
            event_dict["webcasts"] = []

        return event_dict
