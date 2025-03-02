from collections import defaultdict
from typing import cast, Dict, List, NewType

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import TeamKey
from backend.common.queries.dict_converters.converter_base import ConverterBase

EventDetailsDict = NewType("EventDetailsDict", Dict)


class EventDetailsConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        ApiMajorVersion.API_V3: 4,
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
        normalized_oprs = defaultdict(dict)
        if event_details and event_details.matchstats:
            for stat_type, stats in event_details.matchstats.items():
                if stat_type in {"oprs", "dprs", "ccwms"}:
                    for team, value in cast(Dict[TeamKey, float], stats).items():
                        if "frc" not in team:  # Normalize output
                            team = "frc{}".format(team)
                        normalized_oprs[stat_type][team] = value

        normalized_coprs = defaultdict(dict)
        if event_details and event_details.coprs:
            for copr_type, coprs in event_details.coprs.items():
                for team, value in coprs.items():
                    if "frc" not in team:
                        team = "frc{}".format(team)
                    normalized_coprs[copr_type][team] = value

        rankings = {}
        if event_details:
            rankings = event_details.renderable_rankings
        else:
            rankings = {
                "extra_stats_info": [],
                "rankings": [],
                "sort_order_info": None,
            }

        event_details_dict = {
            "alliances": event_details.alliance_selections if event_details else [],
            "district_points": event_details.district_points if event_details else {},
            "regional_champs_pool_points": (
                event_details.regional_champs_pool_points if event_details else {}
            ),
            "insights": (
                event_details.insights if event_details else {"qual": {}, "playoff": {}}
            ),
            "oprs": normalized_oprs if normalized_oprs else {},  # OPRs, DPRs, CCWMs
            "predictions": event_details.predictions if event_details else {},
            "rankings": rankings,
            "coprs": normalized_coprs,
        }

        return EventDetailsDict(event_details_dict)
