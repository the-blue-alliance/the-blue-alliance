from typing import Dict, List, NewType

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_details import EventDetails
from backend.common.queries.dict_converters.converter_base import ConverterBase

EventDetailsDict = NewType("EventDetailsDict", Dict)


class EventDetailsConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        ApiMajorVersion.API_V3: 3,
    }

    @classmethod
    def _convert_list(cls, model_list: List[EventDetails], version: ApiMajorVersion):
        CONVERTERS = {
            3: cls.eventsDetailsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    @classmethod
    def eventsDetailsConverter_v3(cls, event_details: List[EventDetails]):
        return list(map(cls.eventDetailsConverter_v3, event_details))

    @classmethod
    def eventDetailsConverter_v3(cls, event_details: EventDetails) -> EventDetailsDict:
        rankings = {}
        if event_details:
            rankings = event_details.renderable_rankings
        else:
            rankings = {
                "extra_stats_info": [],
                "rankings": None,
                "sort_order_info": None,
            }

        event_details_dict = {
            "alliances": event_details.alliance_selections if event_details else [],
            "district_points": event_details.district_points if event_details else {},
            "insights": event_details.insights
            if event_details
            else {"qual": {}, "playoff": {}},
            "oprs": event_details.matchstats,
            "predictions": event_details.predictions if event_details else {},
            "rankings": rankings,
        }

        return EventDetailsDict(event_details_dict)
