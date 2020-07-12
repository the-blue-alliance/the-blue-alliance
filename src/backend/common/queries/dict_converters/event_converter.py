import datetime
import json
from typing import Dict, List

from google.cloud import ndb
from pyre_extensions import none_throws

from backend.common.consts import playoff_type
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.queries.dict_converters.converter_base import ConverterBase
from backend.common.queries.dict_converters.district_converter import DistrictConverter


class EventConverter(ConverterBase):
    EVENT_DATE_FORMAT_STR = "%Y-%m-%d"

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
        district_future = (
            none_throws(event.district_key).get_async() if event.district_key else None
        )
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
            "district": DistrictConverter(district_future.get_result()).convert(
                ApiMajorVersion.API_V3
            )
            if district_future
            else None,
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

    @classmethod
    def dictToModel_v3(cls, data: Dict) -> Event:
        event = Event(id=data["key"])
        event.name = data["name"]
        event.short_name = data["short_name"]
        event.event_short = data["event_code"]
        event.event_type_enum = data["event_type"]
        event.official = event.event_type_enum in SEASON_EVENT_TYPES
        event.year = data["year"]
        event.timezone_id = data["timezone"]
        event.website = data["website"]
        event.start_date = (
            datetime.datetime.strptime(data["start_date"], cls.EVENT_DATE_FORMAT_STR)
            if data["start_date"]
            else None
        )
        event.end_date = (
            datetime.datetime.strptime(data["end_date"], cls.EVENT_DATE_FORMAT_STR)
            if data["end_date"]
            else None
        )
        event.webcast_json = json.dumps(data["webcasts"])
        event.venue = data["location_name"]
        event.city = data["city"]
        event.state_prov = data["state_prov"]
        event.country = data["country"]
        event.playoff_type = data["playoff_type"]
        event.parent_event = (
            ndb.Key(Event, data["parent_event_key"])
            if data["parent_event_key"]
            else None
        )
        event.divisions = (
            [ndb.Key(Event, div_key) for div_key in data["division_keys"]]
            if data["division_keys"]
            else []
        )

        event.district_key = (
            ndb.Key(District, data["district"]["key"]) if data["district"] else None
        )
        return event
