# Calculates OPR/DPR/CCWM
# For implementation details, see
# https://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from google.cloud import ndb

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.models.keys import TeamId, Year
from backend.common.models.match import Match
from backend.common.models.stats import EventMatchStats, StatType
from backend.common.queries import event_query


TTeamIdMap = Dict[TeamId, int]


class MatchstatsHelper(object):
    @classmethod
    def build_team_mapping(
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
            if match.comp_level != "qm":  # only consider quals matches
                continue
            for alliance_color in ALLIANCE_COLORS:
                for team in match.alliances[alliance_color]["teams"]:
                    team_set.add(team[3:])  # turns "frc254B" into "254B"

        team_list = list(team_set)
        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return team_list, team_id_map

    @classmethod
    def build_Minv_matrix(
        cls, matches: List[Match], team_id_map: TTeamIdMap, played_only: bool = False
    ):

        n = len(team_id_map.keys())
        M = np.zeros([n, n])
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
    def build_s_matrix(
        cls,
        matches: List[Match],
        team_id_map: TTeamIdMap,
        stat_type: StatType,
        init_stats: Optional[Dict[StatType, Dict[TeamId, int]]] = None,
        init_stats_default: int = 0,
        limit_matches: Optional[int] = None,
    ):
        n = len(team_id_map.keys())
        s = np.zeros([n, 1])
        for match in matches:
            if match.comp_level != CompLevel.QM:  # only consider quals matches
                continue

            treat_as_unplayed = (
                limit_matches is not None and match.match_number > limit_matches
            )

            for alliance_color in ALLIANCE_COLORS:
                alliance_teams = [
                    team[3:] for team in match.alliances[alliance_color]["teams"]
                ]
                stat = cls._get_stat(
                    stat_type,
                    match,
                    alliance_color,
                    alliance_teams,
                    init_stats,
                    init_stats_default,
                    treat_as_unplayed,
                )
                for team in alliance_teams:
                    s[team_id_map[team]] += stat
        return s

    @classmethod
    def calc_stat(
        cls,
        matches: List[Match],
        team_list: List[TeamId],
        team_id_map: TTeamIdMap,
        Minv: Any,
        stat_type: StatType,
        init_stats: Optional[Dict[StatType, Dict[TeamId, int]]] = None,
        init_stats_default: int = 0,
        limit_matches: Optional[int] = None,
    ):
        s = cls.build_s_matrix(
            matches,
            team_id_map,
            stat_type,
            init_stats=init_stats,
            init_stats_default=init_stats_default,
            limit_matches=limit_matches,
        )
        x = np.dot(Minv, s)

        stat_dict = {}
        for team, stat in zip(team_list, x):
            stat_dict[team] = stat[0]
        return stat_dict

    @classmethod
    def _get_stat(
        cls,
        stat_type: StatType,
        match: Match,
        alliance_color: AllianceColor,
        alliance_teams: List[TeamId],
        init_stats: Optional[Dict[StatType, Dict[TeamId, int]]],
        init_stats_default: int,
        treat_as_unplayed: bool,
    ) -> Optional[int]:
        match_played = match.has_been_played and not treat_as_unplayed

        if match_played:
            if stat_type == StatType.OPR:
                return match.alliances[alliance_color]["score"]
            elif stat_type == StatType.DPR:
                if alliance_color == AllianceColor.RED:
                    other_alliance_color = AllianceColor.BLUE
                else:
                    other_alliance_color = AllianceColor.RED
                return match.alliances[other_alliance_color]["score"]
            elif stat_type == StatType.CCWM:
                if alliance_color == AllianceColor.RED:
                    other_alliance_color = AllianceColor.BLUE
                else:
                    other_alliance_color = AllianceColor.BLUE
                return (
                    match.alliances[alliance_color]["score"]
                    - match.alliances[other_alliance_color]["score"]
                )

        # None of the above cases were met. Return default.
        if init_stats and stat_type in init_stats:
            total = 0
            for team in alliance_teams:
                total += init_stats[stat_type].get(team, init_stats_default)
            return total
        else:
            total = 0
            for team in alliance_teams:
                total += init_stats_default
            return total

    @classmethod
    def calculate_matchstats(cls, matches: List[Match], year: Year) -> EventMatchStats:
        if not matches:
            return {}

        team_list, team_id_map = cls.build_team_mapping(matches)
        if not team_list:
            return {}
        Minv = cls.build_Minv_matrix(matches, team_id_map, played_only=True)

        oprs_dict = cls.calc_stat(matches, team_list, team_id_map, Minv, StatType.OPR)
        dprs_dict = cls.calc_stat(matches, team_list, team_id_map, Minv, StatType.DPR)
        ccwms_dict = cls.calc_stat(matches, team_list, team_id_map, Minv, StatType.CCWM)

        stats: EventMatchStats = {
            StatType.OPR: oprs_dict,
            StatType.DPR: dprs_dict,
            StatType.CCWM: ccwms_dict,
        }

        return stats

    @classmethod
    def get_last_event_stats(
        cls, team_list: List[TeamId], event_key: ndb.Key
    ) -> EventMatchStats:
        year = int(event_key.id()[:4])
        cur_event = event_key.get()

        # Check cache for stored OPRs
        last_event_stats: EventMatchStats = defaultdict(dict)
        """
        cache_key = '{}:last_event_stats'.format(event_key.id())
        last_event_stats = memcache.get(cache_key)
        if last_event_stats is None:
            last_event_stats = defaultdict(dict)
        """

        # Make necessary queries for missing stats
        futures = []
        for team in team_list:
            if team not in last_event_stats:
                events_future = event_query.TeamYearEventsQuery(
                    "frc{}".format(team), year
                ).fetch_async()
                futures.append((team, events_future))

        # Add missing stats to last_event_stats
        for team, events_future in futures:
            events = events_future.get_result()

            # Find last event before current event
            last_event = None
            last_event_start = None
            for event in events:
                if (
                    event.official
                    and event.start_date < cur_event.start_date
                    and event.event_type_enum != EventType.CMP_FINALS
                ):
                    if last_event is None or event.start_date > last_event_start:
                        last_event = event
                        last_event_start = event.start_date

            if last_event is not None and last_event.matchstats:
                for stat, values in last_event.matchstats.items():
                    if values and team in values:
                        last_event_stats[stat][team] = values[team]

        # memcache.set(cache_key, last_event_stats, 60*60*24)
        return last_event_stats
