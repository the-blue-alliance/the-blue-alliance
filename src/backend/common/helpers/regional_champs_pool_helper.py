import heapq
import logging
from collections import defaultdict
from typing import DefaultDict, Dict, List, NamedTuple, Set, Union

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.award_type import NON_JUDGED_NON_TEAM_AWARDS
from backend.common.consts.district_point_values import DistrictPointValues
from backend.common.futures import TypedFuture
from backend.common.helpers.district_helper import (
    DistrictHelper,
    DistrictRankingTeamTotal,
)
from backend.common.models.event import Event
from backend.common.models.event_district_points import (
    EventDistrictPoints,
    TeamAtEventDistrictPoints,
    TeamAtEventDistrictPointTiebreakers,
)
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.models.team import Team


class RegionalChampsPoolTiebreakers(NamedTuple):
    best_playoff_points: int
    best_alliance_points: int
    best_qual_points: int


class RegionalChampsPoolHelper(DistrictHelper):

    @classmethod
    def calculate_event_points(cls, event: Event) -> EventDistrictPoints:
        event.get_awards_async()
        event.get_matches_async()

        district_points: EventDistrictPoints = {
            "points": defaultdict(
                lambda: TeamAtEventDistrictPoints(
                    qual_points=0,
                    elim_points=0,
                    alliance_points=0,
                    award_points=0,
                    total=0,
                ),
            ),
            "tiebreakers": defaultdict(
                lambda: TeamAtEventDistrictPointTiebreakers(
                    # for tiebreaker stats that can't be calculated with 'points'
                    qual_wins=0,
                    highest_qual_scores=[],
                )
            ),
        }

        # match points
        cls._calc_rank_based_match_points(
            event, district_points, event.matches, POINTS_MULTIPLIER=1
        )

        # alliance points
        if event.alliance_selections:
            selection_points = cls._alliance_selections_to_points(
                event, multiplier=1, alliance_selections=event.alliance_selections
            )
            for team, points in selection_points.items():
                district_points["points"][team]["alliance_points"] += points
        else:
            logging.info(
                "Event {} has no alliance selection regional pool points!".format(
                    event.key.id()
                )
            )

        # award points
        for award in event.awards:
            point_value = 0
            if award.award_type_enum not in NON_JUDGED_NON_TEAM_AWARDS:
                if award.award_type_enum in DistrictPointValues.REGIONAL_AWARD_VALUES:
                    point_value = DistrictPointValues.REGIONAL_AWARD_VALUES.get(
                        award.award_type_enum
                    )
                else:
                    point_value = DistrictPointValues.OTHER_AWARD_DEFAULT

            # Add award points to all teams who won
            if point_value:
                for team in award.team_list:
                    team_key = none_throws(team.string_id())
                    district_points["points"][team_key]["award_points"] += point_value

        for team, point_breakdown in district_points["points"].items():
            total_points = sum(
                [
                    point_breakdown["qual_points"],
                    point_breakdown["elim_points"],
                    point_breakdown["alliance_points"],
                    point_breakdown["award_points"],
                ]
            )
            district_points["points"][team]["total"] += total_points

        return district_points

    @classmethod
    def calculate_rankings(
        cls,
        events: List[Event],
        teams: Union[List[Team], TypedFuture[List[Team]]],
        year: Year,
    ) -> Dict[TeamKey, DistrictRankingTeamTotal]:
        # aggregate points from first two regional events
        events_by_key: Dict[EventKey, Event] = {}
        team_attendance: DefaultDict[TeamKey, List[EventKey]] = defaultdict(list)
        team_totals: Dict[TeamKey, DistrictRankingTeamTotal] = defaultdict(
            lambda: DistrictRankingTeamTotal(
                event_points=[],
                point_total=0,
                rookie_bonus=0,
                tiebreakers=RegionalChampsPoolTiebreakers(
                    best_playoff_points=0,
                    best_alliance_points=0,
                    best_qual_points=0,
                ),
                qual_scores=[],
                other_bonus=0,
            )
        )

        for event in events:
            events_by_key[event.key_name] = event
            event_regional_points = event.regional_champs_pool_points
            if event_regional_points is None:
                continue

            for team_key in set(event_regional_points["points"].keys()).union(
                set(event_regional_points["tiebreakers"].keys())
            ):
                team_attendance[team_key].append(event.key_name)
                if len(team_attendance[team_key]) > 2:
                    continue

                if team_key in event_regional_points["points"]:
                    tiebreakers = RegionalChampsPoolTiebreakers(
                        *team_totals[team_key]["tiebreakers"]
                    )

                    team_event_points: TeamAtEventDistrictPoints = (
                        event_regional_points["points"][team_key]
                    )
                    team_totals[team_key]["event_points"].append(
                        (event, team_event_points)
                    )
                    team_totals[team_key]["point_total"] += team_event_points["total"]
                    tiebreakers = RegionalChampsPoolTiebreakers(
                        best_playoff_points=max(
                            tiebreakers.best_playoff_points,
                            team_event_points["elim_points"],
                        ),
                        best_alliance_points=max(
                            tiebreakers.best_alliance_points,
                            team_event_points["alliance_points"],
                        ),
                        best_qual_points=max(
                            tiebreakers.best_qual_points,
                            team_event_points["qual_points"],
                        ),
                    )

                    team_totals[team_key]["tiebreakers"] = tiebreakers

                if team_key in event_regional_points["tiebreakers"]:
                    team_totals[team_key]["qual_scores"] = heapq.nlargest(
                        3,
                        [
                            *event_regional_points["tiebreakers"][team_key][
                                "highest_qual_scores"
                            ],
                            *team_totals[team_key]["qual_scores"],
                        ],
                    )

        valid_team_keys: Set[TeamKey] = set()
        if isinstance(teams, ndb.tasklets.Future):
            teams = teams.get_result()

        for team in teams:
            if isinstance(teams, ndb.tasklets.Future):
                team = team.get_result()
            bonus = cls._get_rookie_bonus(year, team.rookie_year)

            team_totals[team.key_name]["rookie_bonus"] = bonus
            team_totals[team.key_name]["point_total"] += bonus

            valid_team_keys.add(team.key_name)

        team_totals = dict(
            sorted(
                team_totals.items(),
                key=lambda item: [
                    -item[1]["point_total"],
                ]
                + [-t for t in item[1]["tiebreakers"]]
                + [-score for score in item[1]["qual_scores"]],
            )
        )

        return dict(
            filter(lambda item: item[0] in valid_team_keys, team_totals.items())
        )
