# Calculates OPR/DPR/CCWM
# For implementation details, see
# https://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

from collections import defaultdict, OrderedDict
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import numpy.typing as npt
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import (
    ALLIANCE_COLORS,
    AllianceColor,
    OPPONENT,
)
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.memcache import MemcacheClient
from backend.common.models.event_matchstats import (
    Component,
    EventComponentOPRs,
    TeamStatMap,
)
from backend.common.models.keys import TeamId, Year
from backend.common.models.match import Match
from backend.common.models.stats import EventMatchStats, StatType
from backend.common.queries import event_query

TTeamIdMap = Dict[TeamId, int]
StatAccessor = Callable[[Match, AllianceColor], float]


OPR_ACCESSOR: StatAccessor = lambda match, color: match.alliances[color]["score"]
DPR_ACCESSOR: StatAccessor = lambda match, color: match.alliances[OPPONENT[color]][
    "score"
]
CCWM_ACCESSOR: StatAccessor = (
    lambda match, color: match.alliances[color]["score"]
    - match.alliances[OPPONENT[color]]["score"]
)
MANUAL_COMPONENTS = {
    2019: {
        "Cargo + Panel Points": lambda match, color: (
            match.score_breakdown[color].get("cargoPoints", 0)
            + match.score_breakdown[color].get("hatchPanelPoints", 0)
        )
    },
    2023: {
        "Total Game Piece Count": lambda match, color: (
            match.score_breakdown[color].get("teleopGamePieceCount", 0)
            + match.score_breakdown[color].get("extraGamePieceCount", 0)
        ),
        "Total Game Piece Points": lambda match, color: (
            match.score_breakdown[color].get("autoGamePiecePoints", 0)
            + match.score_breakdown[color].get("teleopGamePiecePoints", 0)
        ),
        "Foul Count Received": lambda match, color: (
            match.score_breakdown[OPPONENT[color]].get("foulCount", 0)
        ),
        "Foul Points Received": lambda match, color: (
            match.score_breakdown[OPPONENT[color]].get("foulPoints", 0)
        ),
        "Total Points Less Fouls": lambda match, color: (
            match.score_breakdown[color].get("totalPoints", 0)
            - match.score_breakdown[color].get("foulPoints", 0)
        ),
        "Total Cones Scored": lambda match, color: (
            sum(
                [
                    match.score_breakdown[color]["teleopCommunity"]["B"].count("Cone"),
                    match.score_breakdown[color]["teleopCommunity"]["M"].count("Cone"),
                    match.score_breakdown[color]["teleopCommunity"]["T"].count("Cone"),
                ]
            )
        ),
        "Total Cubes Scored": lambda match, color: (
            sum(
                [
                    match.score_breakdown[color]["teleopCommunity"]["B"].count("Cube"),
                    match.score_breakdown[color]["teleopCommunity"]["M"].count("Cube"),
                    match.score_breakdown[color]["teleopCommunity"]["T"].count("Cube"),
                ]
            )
        ),
    },
    2024: {
        "Total Mic": lambda match, color: sum(
            [
                match.score_breakdown[color].get("micCenterStage", 0),
                match.score_breakdown[color].get("micStageLeft", 0),
                match.score_breakdown[color].get("micStageRight", 0),
            ]
        ),
        "Total Trap": lambda match, color: sum(
            [
                match.score_breakdown[color].get("trapCenterStage", 0),
                match.score_breakdown[color].get("trapStageLeft", 0),
                match.score_breakdown[color].get("trapStageRight", 0),
            ]
        ),
        "Total Teleop Game Pieces": lambda match, color: sum(
            [
                match.score_breakdown[color].get("teleopAmpNoteCount", 0),
                match.score_breakdown[color].get("teleopSpeakerNoteCount", 0),
                match.score_breakdown[color].get("teleopSpeakerNoteAmplifiedCount", 0),
            ]
        ),
        "Total Auto Game Pieces": lambda match, color: sum(
            [
                match.score_breakdown[color].get("autoAmpNoteCount", 0),
                match.score_breakdown[color].get("autoSpeakerNoteCount", 0),
            ]
        ),
        "Total Overall Game Pieces": lambda match, color: sum(
            [
                match.score_breakdown[color].get("autoAmpNoteCount", 0),
                match.score_breakdown[color].get("autoSpeakerNoteCount", 0),
                match.score_breakdown[color].get("teleopAmpNoteCount", 0),
                match.score_breakdown[color].get("teleopSpeakerNoteCount", 0),
                match.score_breakdown[color].get("teleopSpeakerNoteAmplifiedCount", 0),
            ]
        ),
        "Amplification Rate": lambda match, color: match.score_breakdown[color].get(
            "teleopSpeakerNoteAmplifiedCount", 0
        )
        / max(
            1,
            match.score_breakdown[color].get("teleopSpeakerNoteCount", 0)
            + match.score_breakdown[color].get("teleopSpeakerNoteAmplifiedCount", 0),
        ),
    },
    2025: {
        "L1 Coral Count": lambda match, color: (
            match.score_breakdown[color].get("autoReef", {}).get("trough", 0)
            + match.score_breakdown[color].get("teleopReef", {}).get("trough", 0)
        ),
        "L2 Coral Count": lambda match, color: (
            match.score_breakdown[color].get("teleopReef", {}).get("tba_botRowCount", 0)
        ),
        "L3 Coral Count": lambda match, color: (
            match.score_breakdown[color].get("teleopReef", {}).get("tba_midRowCount", 0)
        ),
        "L4 Coral Count": lambda match, color: (
            match.score_breakdown[color].get("teleopReef", {}).get("tba_topRowCount", 0)
        ),
        "Total Coral Count": lambda match, color: sum(
            [
                match.score_breakdown[color].get("autoCoralCount", 0),
                match.score_breakdown[color].get("teleopCoralCount", 0),
            ]
        ),
        "Total Coral Points": lambda match, color: sum(
            [
                match.score_breakdown[color].get("autoCoralPoints", 0),
                match.score_breakdown[color].get("teleopCoralPoints", 0),
            ]
        ),
        "Total Algae Count": lambda match, color: sum(
            [
                match.score_breakdown[color].get("wallAlgaeCount", 0),
                match.score_breakdown[color].get("netAlgaeCount", 0),
            ]
        ),
        "Total Game Piece Count": lambda match, color: sum(
            [
                match.score_breakdown[color].get("autoCoralCount", 0),
                match.score_breakdown[color].get("teleopCoralCount", 0),
                match.score_breakdown[color].get("wallAlgaeCount", 0),
                match.score_breakdown[color].get("netAlgaeCount", 0),
            ]
        ),
    },
    2026: {
        "Hub Auto Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("autoCount", 0),
        "Hub Teleop Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("teleopCount", 0),
        "Hub Endgame Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("endgameCount", 0),
        "Hub Total Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("totalCount", 0),
        "Hub Transition Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("transitionCount", 0),
        "Hub Shift 1 Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("shift1Count", 0),
        "Hub Shift 2 Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("shift2Count", 0),
        "Hub Shift 3 Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("shift3Count", 0),
        "Hub Shift 4 Fuel Count": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("shift4Count", 0),
        "Hub First Active Shift Count": lambda match, color: (
            match.score_breakdown[color]["hubScore"].get("shift1Count", 0)
            + match.score_breakdown[color]["hubScore"].get("shift2Count", 0)
        ),
        "Hub Second Active Shift Count": lambda match, color: (
            match.score_breakdown[color]["hubScore"].get("shift3Count", 0)
            + match.score_breakdown[color]["hubScore"].get("shift4Count", 0)
        ),
        "Hub Uncounted": lambda match, color: match.score_breakdown[color][
            "hubScore"
        ].get("uncounted", 0),
    },
}


def make_default_component_accessor(component: Component) -> StatAccessor:
    return lambda match, color: float(match.score_breakdown[color].get(component, 0))


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
        cls, matches: List[Match], team_id_map: TTeamIdMap
    ) -> npt.NDArray[np.float64]:
        n = len(team_id_map.keys())
        M = np.zeros((n, n))
        for match in matches:
            # only consider quals matches that have been played
            if (match.comp_level != CompLevel.QM) or (not match.has_been_played):
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
        stat_accessor: StatAccessor,
    ) -> npt.NDArray[np.float64]:
        n = len(team_id_map.keys())
        s = np.zeros((n, 1))
        for match in matches:
            # only consider quals matches that have been played
            if (match.comp_level != CompLevel.QM) or (not match.has_been_played):
                continue

            for alliance_color in ALLIANCE_COLORS:
                alliance_teams = [
                    team[3:] for team in match.alliances[alliance_color]["teams"]
                ]
                stat = stat_accessor(match, alliance_color)
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
        stat_accessor: StatAccessor,
    ) -> TeamStatMap:
        s = cls.build_s_matrix(
            matches,
            team_id_map,
            stat_accessor,
        )
        x = np.dot(Minv, s)

        stat_dict = {}
        for team, stat in zip(team_list, x):
            stat_dict[team] = stat[0]
        return stat_dict

    @classmethod
    def calculate_matchstats(cls, matches: List[Match], year: Year) -> EventMatchStats:
        if not matches:
            return {}

        team_list, team_id_map = cls.build_team_mapping(matches)
        if not team_list:
            return {}
        Minv = cls.build_Minv_matrix(matches, team_id_map)

        oprs_dict = cls.calc_stat(matches, team_list, team_id_map, Minv, OPR_ACCESSOR)
        dprs_dict = cls.calc_stat(matches, team_list, team_id_map, Minv, DPR_ACCESSOR)
        ccwms_dict = cls.calc_stat(matches, team_list, team_id_map, Minv, CCWM_ACCESSOR)

        stats: EventMatchStats = {
            StatType.OPR: oprs_dict,
            StatType.DPR: dprs_dict,
            StatType.CCWM: ccwms_dict,
        }

        return stats

    @classmethod
    def calculate_coprs(cls, matches: List[Match], year: Year) -> EventComponentOPRs:
        coprs: OrderedDict[Component, TeamStatMap] = OrderedDict()
        matches_with_score_breakdown = [
            match for match in matches if match.score_breakdown is not None
        ]

        if len(matches_with_score_breakdown) == 0:
            return coprs

        first_match = matches_with_score_breakdown[0]

        team_list, team_id_map = cls.build_team_mapping(matches_with_score_breakdown)
        if not team_list:
            return {}

        Minv = cls.build_Minv_matrix(matches_with_score_breakdown, team_id_map)

        if year in MANUAL_COMPONENTS.keys():
            for name, accessor in MANUAL_COMPONENTS[year].items():
                coprs[name] = cls.calc_stat(
                    matches_with_score_breakdown, team_list, team_id_map, Minv, accessor
                )

        # For each k-v in score_breakdown, attempt to convert v to a float.
        # If we can't do that, we can't calculate a component OPR for it.
        # As such, this will calculate cOPRs for any int/float/bool field.
        # Use red on the first match just to get all the score_breakdown keys available.
        for component, value in none_throws(first_match.score_breakdown)[
            AllianceColor.RED
        ].items():
            try:
                float(value)
            except (ValueError, TypeError):
                pass
            else:
                coprs[component] = cls.calc_stat(
                    matches_with_score_breakdown,
                    team_list,
                    team_id_map,
                    Minv,
                    make_default_component_accessor(component),
                )

        return coprs

    @classmethod
    def get_last_event_stats(
        cls, team_list: List[TeamId], event_key: ndb.Key
    ) -> EventMatchStats:
        year = int(none_throws(event_key.string_id())[:4])
        cur_event = event_key.get()

        # Check cache for stored OPRs
        last_event_stats: EventMatchStats = defaultdict(dict)

        memcache = MemcacheClient.get()
        cache_key = f"{event_key.id()}:last_event_stats".encode()
        last_event_stats = memcache.get(cache_key)
        if last_event_stats is None:
            last_event_stats = defaultdict(dict)

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

        memcache.set(cache_key, last_event_stats, 60 * 60 * 24)
        return last_event_stats
