# Calculates OPR/DPR/CCWM
# For implementation details, see
# https://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

from collections import OrderedDict
from typing import Callable, Dict, List, Tuple

import numpy as np
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import (
    ALLIANCE_COLORS,
    AllianceColor,
    OPPONENT,
)
from backend.common.consts.comp_level import CompLevel
from backend.common.models.event_matchstats import (
    Component,
    EventMatchstats,
    StatType,
    TeamStatMap,
)
from backend.common.models.keys import TeamId
from backend.common.models.match import Match

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
        lambda match, color: float(match.score_breakdown[color].get(comp, 0))
    )

    EVERGREEN: Dict[StatType, StatAccessor] = {
        StatType.OPR: OPR_ACCESSOR,
        StatType.DPR: DPR_ACCESSOR,
        StatType.CCWM: CCWM_ACCESSOR,
    }

    COMPONENTS = {
        2020: {
            "Total Power Cell Points": lambda match, color: (
                match.score_breakdown[color].get("autoCellPoints")
                + match.score_breakdown[color].get("teleopCellPoints")
            ),
        },
        2019: {
            "Cargo + Panel Points": lambda match, color: (
                match.score_breakdown[color].get("cargoPoints")
                + match.score_breakdown[color].get("hatchPanelPoints")
            )
        },
    }

    @classmethod
    def calculate_matchstats(
        cls, matches: List[Match], skip_coprs: bool = False
    ) -> EventMatchstats:
        return EventMatchstats(
            oprs=cls.calculate_oprs(matches),
            dprs=cls.calculate_dprs(matches),
            ccwms=cls.calculate_ccwms(matches),
            coprs={} if skip_coprs else cls.calculate_coprs(matches),
        )

    @classmethod
    def calculate_oprs(cls, matches: List[Match]) -> TeamStatMap:
        return cls.calculate_stat(matches, cls.OPR_ACCESSOR)

    @classmethod
    def calculate_dprs(cls, matches: List[Match]) -> TeamStatMap:
        return cls.calculate_stat(matches, cls.DPR_ACCESSOR)

    @classmethod
    def calculate_ccwms(cls, matches: List[Match]) -> TeamStatMap:
        return cls.calculate_stat(matches, cls.CCWM_ACCESSOR)

    @classmethod
    def calculate_coprs(cls, matches: List[Match]) -> Dict[Component, TeamStatMap]:
        coprs = OrderedDict()

        # If there is not valid data for COPRs, skip
        if not (
            matches is not None
            and len(matches) > 0
            and matches[0].score_breakdown is not None
        ):
            return coprs

        # Specific components specified in cls
        year = matches[0].year
        if year in cls.COMPONENTS.keys():
            for title, accessor in cls.COMPONENTS[year].items():
                coprs[title] = cls.calculate_stat(matches, accessor)

        # for each string-like key in the score_breakdown object
        # (just take the red score_breakdown from match 0, it's an arbitrary selection)
        for component, value in none_throws(matches[0].score_breakdown)[
            AllianceColor.RED
        ].items():
            try:
                float(value)
            except ValueError:
                pass
                # Can't convert the given score_breakdown value to a float, so we can't calculate a component OPR for it
            else:
                coprs[component] = cls.calculate_stat(
                    matches, cls.DEFAULT_COMPONENT_ACCESSOR(component)
                )

        return coprs

    @classmethod
    def calculate_stat(
        cls,
        matches: List[Match],
        point_accessor: StatAccessor,
    ) -> TeamStatMap:
        if not matches:
            return {}

        team_list, team_id_map = cls._build_team_mapping(matches)
        if not team_list:
            return {}

        M_inv = cls._build_M_inv_matrix(matches, team_id_map, played_only=True)

        return {
            f"frc{k}": v
            for k, v in cls._calc_stat(
                matches, team_list, team_id_map, M_inv, point_accessor
            ).items()
        }

    @classmethod
    def _build_team_mapping(
        cls, matches: List[Match]
    ) -> Tuple[List[TeamId], TTeamIdMap]:
        """
        Returns (team_list, team_id_map)
        team_list: A list of team_str such as '254' or '254B'
        team_id_map: A dict of key: team_str, value: row index in x_matrix that corresponds to the team
        """
        # Build team list
        team_set = set()
        for match in matches:
            if match.comp_level != CompLevel.QM:  # only consider quals matches
                continue
            for alliance_color in ALLIANCE_COLORS:
                for team in match.alliances[alliance_color]["teams"]:
                    team_set.add(team[3:])  # turns "frc254B" into "254B"

        team_list = list(team_set)  # Keep enumerate ordering by converting to list
        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return team_list, team_id_map

    @classmethod
    def _build_M_inv_matrix(
        cls,
        matches: List[Match],
        team_id_map: TTeamIdMap,
        played_only: bool = False,
    ) -> "np.ndarray[float]":
        n = len(team_id_map.keys())
        M = np.zeros((n, n))
        for match in matches:
            if match.comp_level != CompLevel.QM:  # only consider quals matches
                continue
            if played_only and not match.has_been_played:
                continue
            for alliance_color in ALLIANCE_COLORS:
                alliance_teams = match.alliances[alliance_color]["teams"]
                for team1 in alliance_teams:
                    team1_id = team_id_map[team1[3:]]
                    for team2 in alliance_teams:
                        M[team1_id, team_id_map[team2[3:]]] += 1
        return np.linalg.pinv(M)

    @classmethod
    def _build_s_matrix(
        cls,
        matches: List[Match],
        team_id_map: TTeamIdMap,
        point_accessor: StatAccessor,
    ) -> "np.ndarray[float]":
        n = len(team_id_map.keys())
        s = np.zeros((n, 1))
        for match in matches:
            if match.comp_level != CompLevel.QM:  # only consider quals matches
                continue

            for alliance_color in ALLIANCE_COLORS:
                alliance_teams = [
                    team[3:] for team in match.alliances[alliance_color]["teams"]
                ]

                stat = point_accessor(match, alliance_color)
                for team in alliance_teams:
                    s[team_id_map[team]] += stat

        return s

    @classmethod
    def _calc_stat(
        cls,
        matches: List[Match],
        team_list: List[TeamId],
        team_id_map: TTeamIdMap,
        M_inv: np.ndarray,
        point_accessor: StatAccessor,
    ):
        s = cls._build_s_matrix(
            matches,
            team_id_map,
            point_accessor,
        )
        x = np.dot(M_inv, s)

        stat_dict = {}
        for team, stat in zip(team_list, x):
            stat_dict[team] = stat[0]

        return stat_dict
