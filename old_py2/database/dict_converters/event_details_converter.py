from collections import defaultdict
from database.dict_converters.converter_base import ConverterBase


class EventDetailsConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 3,
    }

    @classmethod
    def _convert(cls, event_details, dict_version):
        CONVERTERS = {
            3: cls.eventsDetailsConverter_v3,
        }
        return CONVERTERS[dict_version](event_details)

    @classmethod
    def eventsDetailsConverter_v3(cls, event_details):
        event_details = map(cls.eventDetailsConverter_v3, event_details)
        return event_details

    @classmethod
    def eventDetailsConverter_v3(cls, event_details):
        normalized_oprs = defaultdict(dict)
        if event_details and event_details.matchstats:
            for stat_type, stats in event_details.matchstats.items():
                if stat_type in {'oprs', 'dprs', 'ccwms'}:
                    for team, value in stats.items():
                        if 'frc' not in team:  # Normalize output
                            team = 'frc{}'.format(team)
                        normalized_oprs[stat_type][team] = value

        event_details.matchstats if event_details else None
        rankings = {}
        if event_details:
            rankings = event_details.renderable_rankings
        else:
            rankings = {
                "extra_stats_info": [],
                "rankings": None,
                "sort_order_info": None
            }

        event_details_dict = {
            'alliances': event_details.alliance_selections if event_details else [],
            'district_points': event_details.district_points if event_details else {},
            'insights': event_details.insights if event_details else {'qual': {}, 'playoff': {}},
            'oprs': normalized_oprs if normalized_oprs else {},  # OPRs, DPRs, CCWMs
            'predictions': event_details.predictions if event_details else {},
            'rankings': rankings
        }

        return event_details_dict
