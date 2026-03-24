import heapq
import logging
from collections import defaultdict
from typing import cast, DefaultDict, Dict, List, NamedTuple, Optional, Set, Union

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
    EventRegionalChampsPoolPoints,
    TeamAtEventDistrictPoints,
    TeamAtEventDistrictPointTiebreakers,
    TeamAtEventRegionalChampsPoolPoints,
)
from backend.common.models.keys import TeamKey, Year
from backend.common.models.team import Team


class RegionalChampsPoolTiebreakers(NamedTuple):
    best_playoff_points: int
    best_alliance_points: int
    best_qual_points: int


class RegionalChampsPoolHelper(DistrictHelper):

    @classmethod
    def calculate_event_points(cls, event: Event) -> EventRegionalChampsPoolPoints:
        event.prep_awards()
        event.prep_matches()

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

        # Team age points are awarded at each regional event attended.
        rookie_points = cls._get_event_level_rookie_bonus_points(
            event, set(district_points["points"].keys()), multiplier=1
        )
        regional_points = cast(EventRegionalChampsPoolPoints, district_points)
        for team_key, rookie_bonus in rookie_points.items():
            team_points = cast(
                TeamAtEventRegionalChampsPoolPoints,
                regional_points["points"][team_key],
            )
            team_points["rookie_bonus"] = rookie_bonus
            team_points["total"] += rookie_bonus

        return regional_points

    @classmethod
    def calculate_rankings(
        cls,
        events: List[Event],
        teams: Union[List[Team], TypedFuture[List[Team]]],
        year: Year,
        adjustments: Optional[Dict[TeamKey, int]],
    ) -> Dict[TeamKey, DistrictRankingTeamTotal]:
        # aggregate points from first two regional events
        team_attendance: DefaultDict[TeamKey, List[str]] = defaultdict(list)
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
                single_event_bonus=0,
                adjustments=0,
            )
        )

        for event in events:
            event_regional_points = event.regional_champs_pool_points
            if event_regional_points is None:
                continue

            for team_key in set(event_regional_points["points"].keys()).union(
                set(event_regional_points["tiebreakers"].keys())
            ):
                team_attendance[team_key].append(event.key_name)

                num_events = len(team_attendance[team_key])
                if num_events > 2:
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

        if isinstance(teams, ndb.tasklets.Future):
            teams = teams.get_result()

        valid_team_keys: Set[TeamKey] = set()
        for team_f in teams:
            if isinstance(team_f, ndb.tasklets.Future):
                team = team_f.get_result()
            else:
                team = team_f
            team_total = team_totals[team.key_name]
            num_events_attended = len(team_total["event_points"])
            total_rookie_bonus = sum(
                cast(TeamAtEventRegionalChampsPoolPoints, event_points).get(
                    "rookie_bonus", 0
                )
                for _, event_points in team_total["event_points"]
            )

            # Single-Event regional teams are award additional points
            # based on event 1 performance.
            # E2 points = 0.6 * (E1 points) + 14
            # Team age points are included in event-level totals.
            # See section 12.3.1 of the 2025 game manual.
            if num_events_attended == 1:
                first_event_points = team_total["event_points"][0][1]
                single_event_bonus = round(0.6 * first_event_points["total"]) + 14
                team_total["single_event_bonus"] = single_event_bonus
                team_total["point_total"] += single_event_bonus

            team_total["rookie_bonus"] = total_rookie_bonus

            # For other adjustments made by HQ
            if adjustments and (team_adjustment := adjustments.get(team.key_name)):
                team_total["adjustments"] = team_adjustment
                team_total["point_total"] += team_adjustment

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
