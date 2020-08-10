from typing import Dict, Callable, List

from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.match import Match
from backend.common.helpers.opr_helper import OPRHelper


def get_opp_color(color: AllianceColor) -> AllianceColor:
    return [AllianceColor.RED, AllianceColor.BLUE][color == AllianceColor.RED]


class MatchstatsHelper:
    EVERGREEN: Dict[str, Callable[[Match, AllianceColor], float]] = {
        "oprs": lambda match, color: match.alliances[color]["score"],
        "dprs": lambda match, color: match.alliances[get_opp_color(color)]["score"],
        "ccwms": lambda match, color: (
                match.alliances[color]["score"]
                - match.alliances[get_opp_color(color)]["score"]
        ),
    }

    COMPONENTS = {
        2020: {
            "Foul Points": lambda match, color: match.score_breakdown[color].get(
                "foulPoints", 0
            )
        }
    }

    component_default = lambda comp: (
        lambda match, color: match.score_breakdown[color].get(comp, 0)
    )

    @classmethod
    def calculate_matchstats(cls, matches: List[Match]):
        return_val = {k: OPRHelper.calculate_opr(matches, v) for k, v in cls.EVERGREEN.items()}

        # Base components
        coprs = {}
        for component, value in matches[0].score_breakdown[AllianceColor.RED].items():
            if isinstance(value, int) or isinstance(value, float):
                coprs[component] = OPRHelper.calculate_opr(
                    matches, cls.component_default(component)
                )

        return_val['coprs'] = coprs
        return return_val
