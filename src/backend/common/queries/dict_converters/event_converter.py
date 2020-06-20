from typing import Dict, List

from pyre_extensions import none_throws

from backend.common.consts import playoff_type
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event import Event
from backend.common.queries.dict_converters.converter_base import ConverterBase


class EventConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 6,
    # }  TODO: used for cache clearing

    def _convert_list(
        self, model_list: List[Event], version: ApiMajorVersion
    ) -> List[Dict]:
        CONVERTERS = {
            ApiMajorVersion.API_V3: self.eventsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    def eventsConverter_v3(self, events: List[Event]) -> List[Dict]:
        return list(map(self.eventConverter_v3, events))

    def eventConverter_v3(self, event: Event) -> Dict:
        # district_future = event.district_key.get_async() if event.district_key else None
        event_dict = {
            "key": event.key.id(),
            "name": event.name,
            "short_name": event.short_name,
            "event_code": event.event_short,
            "event_type": event.event_type_enum,
            "event_type_string": event.event_type_str,
            "parent_event_key": none_throws(event.parent_event).id()
            if event.parent_event
            else None,
            "playoff_type": event.playoff_type,
            "playoff_type_string": playoff_type.TYPE_NAMES.get(
                playoff_type.PlayoffType(event.playoff_type)
            )
            if event.playoff_type
            else None,
            # "district": DistrictConverter.convert(district_future.get_result(), 3)
            # if district_future
            # else None,
            "division_keys": [
                key.id() for key in event.divisions
            ],  # Datastore stub needs to support repeated properties 2020-06-16 @fangeugene
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
