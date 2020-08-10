# taken from https://github.com/the-blue-alliance/the-blue-alliance/blob/bd16a7daf19774a2dc84509f71fa786c45d0a99e/old_py2/helpers/matchstats_helper.py

# Calculates OPR/DPR/CCWM
# For implementation details, see
# https://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

import numpy as np

from typing import List, Dict, Union, Tuple, Callable
from backend.common.models.match import Match
from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.keys import TeamKey


class OPRHelper:
    @classmethod
    def build_team_mapping(
        cls, matches: List[Match]
    ) -> Tuple[List[TeamKey], Dict[TeamKey, int]]:
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
            for alliance_color in [AllianceColor.RED, AllianceColor.BLUE]:
                for team in match.alliances[alliance_color]["teams"]:
                    team_list.add(team[3:])  # turns "frc254B" into "254B"

        team_list = list(team_list)
        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return team_list, team_id_map

    @classmethod
    def build_m_inv_matrix(
        cls,
        matches: List[Match],
        team_id_map: Dict[TeamKey, int],
        played_only: bool = False,
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
    def build_s_matrix(
        cls,
        matches: List[Match],
        team_id_map: Dict[TeamKey, int],
        point_accessor: Callable[[Match, AllianceColor], float],
    ):

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
    def calc_stat(
        cls,
        matches: List[Match],
        team_list: List[TeamKey],
        team_id_map: Dict[TeamKey, int],
        m_inv: np.ndarray,
        point_accessor: Callable[[Match, AllianceColor], float],
    ):
        s = cls.build_s_matrix(matches, team_id_map, point_accessor,)
        x = np.dot(m_inv, s)

        stat_dict = {}
        for team, stat in zip(team_list, x):
            stat_dict[team] = stat[0]
        return stat_dict

    @classmethod
    def calculate_opr(cls, matches: List[Match], point_accessor: Callable[[Match, AllianceColor], float]):
        if not matches:
            return {}

        team_list, team_id_map = cls.build_team_mapping(matches)
        if not team_list:
            return {}

        m_inv = cls.build_m_inv_matrix(matches, team_id_map, played_only=True)
        d = cls.calc_stat(matches, team_list, team_id_map, m_inv, point_accessor)
        return d

    @classmethod
    def calculate_matchstats(
        cls, matches: List[Match], year: int
    ) -> Dict[str, Union[Dict[TeamKey, float], Dict[str, Dict[TeamKey, float]]]]:
        """
        return type:
        Dict[
            str,  # any of "oprs", "dprs", "ccwms", "coprs"
            Union[  # either
                Dict[str, float],  # simple team:float OPR dict
                Dict[str, Dict[str, float]]  # cOPR dict for component:Dict[team:float]
            ]
        ]
        """
        if not matches:
            return {}

        team_list, team_id_map = cls.build_team_mapping(matches)
        if not team_list:
            return {}

        m_inv = cls.build_m_inv_matrix(matches, team_id_map, played_only=True)

        oprs_dict = cls.calc_stat(matches, team_list, team_id_map, m_inv, "oprs")
        dprs_dict = cls.calc_stat(matches, team_list, team_id_map, m_inv, "dprs")
        ccwms_dict = cls.calc_stat(matches, team_list, team_id_map, m_inv, "ccwms")

        coprs_dict = {}
        for component in matches[0].score_breakdown[AllianceColor.RED].keys():
            coprs_dict[component] = cls.calc_stat(
                matches, team_list, team_id_map, m_inv, component
            )

        stats = {
            "oprs": oprs_dict,
            "dprs": dprs_dict,
            "ccwms": ccwms_dict,
            "coprs": coprs_dict,
        }

        return stats
