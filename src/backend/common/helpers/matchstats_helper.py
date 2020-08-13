# Calculates OPR/DPR/CCWM
# For implementation details, see
# https://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

from typing import Dict, Callable, List
from typing import Tuple

import numpy as np

from backend.common.consts.alliance_color import ALLIANCE_COLORS
from backend.common.consts.alliance_color import AllianceColor, OPPONENT
from backend.common.models.keys import TeamId
from backend.common.models.match import Match
from backend.common.models.stats import StatType, EventMatchStats, Component

StatAccessor = Callable[[Match, AllianceColor], float]
TTeamIdMap = Dict[TeamId, int]


class MatchstatsHelper:
    OPR_ACCESSOR: StatAccessor = lambda match, color: match.alliances[color]["score"]
    DPR_ACCESSOR: StatAccessor = lambda match, color: match.alliances[OPPONENT[color]][
        "score"
    ]
    CCWM_ACCESSOR: StatAccessor = lambda match, color: (
        match.alliances[color]["score"] - match.alliances[OPPONENT[color]]["score"]
    )
    DEFAULT_COMPONENT_ACCESSOR: Callable[[Component], StatAccessor] = lambda comp: (
        lambda match, color: match.score_breakdown[color].get(comp, 0)
    )

    EVERGREEN: Dict[StatType, StatAccessor] = {
        "oprs": OPR_ACCESSOR,
        "dprs": DPR_ACCESSOR,
        "ccwms": CCWM_ACCESSOR,
    }

    COMPONENTS = {
        2020: {
            "Foul Points": lambda match, color: match.score_breakdown[color].get(
                "foulPoints", 0
            ),
            "Auton div Total": lambda match, color: (
                match.score_breakdown[color].get("autoPoints", 0)
                / max(match.score_breakdown[color].get("totalPoints", 0), 1)
            ),
        }
    }

    @classmethod
    def calculate_matchstats(cls, matches: List[Match]) -> EventMatchStats:
        return_val: EventMatchStats = {}
        for stat_type, accessor in cls.EVERGREEN.items():
            stat_dict = cls.calculate_opr(matches, accessor)
            if stat_dict != {}:
                return_val[stat_type] = stat_dict

        # Base components
        coprs = {}
        # Force generators to be lists via len? Not sure if necessary
        # Ran into some errors on 2006cur without it
        if (
            matches is not None
            and len(list(matches)) > 0
            and matches[0].score_breakdown is not None
        ):
            for component, value in (
                matches[0].score_breakdown[AllianceColor.RED].items()
            ):
                if isinstance(value, int) or isinstance(value, float):
                    coprs[component] = cls.calculate_opr(
                        matches, cls.DEFAULT_COMPONENT_ACCESSOR(component)
                    )

            return_val["coprs"] = coprs

            # Specific components
            coprs = {}
            year = matches[0].year
            if year in cls.COMPONENTS:
                for title, fn in cls.COMPONENTS[year].items():
                    coprs[title] = cls.calculate_opr(matches, fn)

                return_val["coprs"].update(coprs)

        return return_val

    @classmethod
    def __build_team_mapping(
        cls, matches: List[Match]
    ) -> Tuple[List[TeamId], TTeamIdMap]:
        """
        Returns (team_list, team_id_map)
        team_list: A list of team_str such as '254' or '254B'
        team_id_map: A dict of key: team_str, value: row index in x_matrix that corresponds to the team
        """
        # Build team list
        team_list = set()
        for match in matches:
            if match.comp_level != "qm":  # only consider quals matches
                continue
            for alliance_color in ALLIANCE_COLORS:
                for team in match.alliances[alliance_color]["teams"]:
                    team_list.add(team[3:])  # turns "frc254B" into "254B"

        team_list = list(team_list)
        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return team_list, team_id_map

    @classmethod
    def __build_m_inv_matrix(
        cls, matches: List[Match], team_id_map: TTeamIdMap, played_only: bool = False,
    ) -> np.ndarray:
        n = len(team_id_map.keys())
        m = np.zeros([n, n])
        for match in matches:
            if match.comp_level != "qm":  # only consider quals matches
                continue
            if played_only and not match.has_been_played:
                continue
            for alliance_color in [AllianceColor.RED, AllianceColor.BLUE]:
                alliance_teams = match.alliances[alliance_color]["teams"]
                for team1 in alliance_teams:
                    team1_id = team_id_map[team1[3:]]
                    for team2 in alliance_teams:
                        m[team1_id, team_id_map[team2[3:]]] += 1

        return np.linalg.pinv(m)

    @classmethod
    def __build_s_matrix(
        cls,
        matches: List[Match],
        team_id_map: TTeamIdMap,
        point_accessor: Callable[[Match, AllianceColor], float],
    ) -> np.ndarray:
        n = len(team_id_map.keys())
        s = np.zeros([n, 1])
        for match in matches:
            if match.comp_level != "qm":  # only consider quals matches
                continue

            for alliance_color in [AllianceColor.RED, AllianceColor.BLUE]:
                alliance_teams = [
                    team[3:] for team in match.alliances[alliance_color]["teams"]
                ]

                stat = point_accessor(match, alliance_color)
                for team in alliance_teams:
                    s[team_id_map[team]] += float(stat)

        return s

    @classmethod
    def __calc_stat(
        cls,
        matches: List[Match],
        team_list: List[TeamId],
        team_id_map: TTeamIdMap,
        m_inv: np.ndarray,
        point_accessor: Callable[[Match, AllianceColor], float],
    ):
        s = cls.__build_s_matrix(matches, team_id_map, point_accessor,)
        x = np.dot(m_inv, s)

        stat_dict = {}
        for team, stat in zip(team_list, x):
            stat_dict[team] = stat[0]
        return stat_dict

    @classmethod
    def calculate_opr(
        cls,
        matches: List[Match],
        point_accessor: Callable[[Match, AllianceColor], float],
    ):
        if not matches:
            return {}

        team_list, team_id_map = cls.__build_team_mapping(matches)
        if not team_list:
            return {}

        m_inv = cls.__build_m_inv_matrix(matches, team_id_map, played_only=True)
        return cls.__calc_stat(matches, team_list, team_id_map, m_inv, point_accessor)
