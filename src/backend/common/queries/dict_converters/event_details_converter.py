from collections import defaultdict
from typing import cast, Dict, List, Union

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import TeamKey
from backend.common.queries.dict_converters.converter_base import ConverterBase


class EventDetailsConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 3,
    # }

    def _convert_list(self, model_list: List[EventDetails], version: ApiMajorVersion):
        CONVERTERS = {
            3: self.eventsDetailsConverter_v3,
        }
        return CONVERTERS[version](model_list)

    @staticmethod
    def _add_frc_str_to_keys(d: Dict[Union[str, int], float]) -> Dict[str, float]:
        normalized = {}
        for team, value in d.items():
            if "frc" not in str(team):
                normalized[f"frc{team}"] = value

        return normalized

    def eventsDetailsConverter_v3(self, event_details: List[EventDetails]):
        return list(map(self.eventDetailsConverter_v3, event_details))

    def eventDetailsConverter_v3(self, event_details: EventDetails) -> Dict:
        normalized_oprs = defaultdict(dict)
        if event_details and event_details.matchstats:
            for stat_type, stats in event_details.matchstats.items():
                stats = cast(Dict[TeamKey, float], stats)
                if stat_type in {"oprs", "dprs", "ccwms"}:
                    normalized_oprs[
                        stat_type
                    ] = EventDetailsConverter._add_frc_str_to_keys(stats)

                if stat_type == "coprs":
                    for component, component_oprs in stats.items():
                        normalized_oprs[stat_type][
                            component
                        ] = EventDetailsConverter._add_frc_str_to_keys(stats)

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
            "oprs": normalized_oprs if normalized_oprs else {},  # OPRs, DPRs, CCWMs
            "predictions": event_details.predictions if event_details else {},
            "rankings": rankings,
        }

        return event_details_dict
