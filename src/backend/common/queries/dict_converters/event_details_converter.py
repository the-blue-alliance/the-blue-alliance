from typing import Dict, List, Union

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_details import EventDetails
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

        return event_details_dict
