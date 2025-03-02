import heapq
import logging
import math
from collections import defaultdict
from datetime import timedelta
from typing import (
    cast,
    DefaultDict,
    Dict,
    List,
    NamedTuple,
    Sequence,
    Set,
    Tuple,
    TypedDict,
    Union,
)

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.award_type import AwardType, NON_JUDGED_NON_TEAM_AWARDS
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.district_point_values import DistrictPointValues
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.futures import TypedFuture
from backend.common.helpers.match_helper import (
    MatchHelper,
)
from backend.common.helpers.playoff_advancement_helper import (
    PlayoffAdvancementHelper,
)
from backend.common.models.alliance import EventAlliance
from backend.common.models.event import Event
from backend.common.models.event_district_points import (
    EventDistrictPoints,
    TeamAtEventDistrictPoints,
    TeamAtEventDistrictPointTiebreakers,
)
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.models.match import Match
from backend.common.models.team import Team


class DistrictRankingTeamTotal(TypedDict):
    """
    This is used internally in DistrictHelper to compute ranking components per-team
    """

    event_points: List[Tuple[Event, TeamAtEventDistrictPoints]]
    point_total: int
    tiebreakers: Sequence[int]
    qual_scores: List[int]
    rookie_bonus: int
    other_bonus: int


class DistrictRankingTiebreakers(NamedTuple):
    total_playoff_points: int
    best_playoff_points: int
    total_alliance_points: int
    best_alliance_points: int
    total_qual_points: int


class DistrictHelper:
    """
    Point calculations based on:
    2014: http://www.usfirst.org/sites/default/files/uploadedFiles/Robotics_Programs/FRC/Resources/FRC_District_Standard_Points_Ranking_System.pdf
    2015: http://www.usfirst.org/sites/default/files/uploadedFiles/Robotics_Programs/FRC/Game_and_Season__Info/2015/FRC_District_Standard_Points_Ranking_System_2015%20Summary.pdf
    2016: https://firstfrc.blob.core.windows.net/frc2016manuals/AdminManual/FRC-2016-admin-manual.pdf
    """

    @classmethod
    def inverf(cls, x: float) -> float:
        if x > 0:
            s = 1
        elif x < 0:
            s = -1
        else:
            s = 0
        a = 0.147
        y = s * math.sqrt(
            (
                math.sqrt(
                    (((2 / (math.pi * a)) + ((math.log(1 - x**2)) / 2)) ** 2)
                    - ((math.log(1 - x**2)) / a)
                )
            )
            - ((2 / (math.pi * a)) + (math.log(1 - x**2)) / 2)
        )
        return y

    @classmethod
    def calculate_event_points(cls, event: Event) -> EventDistrictPoints:
        event.get_awards_async()
        event.get_matches_async()

        # Typically 3 for District CMP, 1 otherwise
        use_dcmp_multiplier = (
            event.event_type_enum == EventType.DISTRICT_CMP
            or event.event_type_enum == EventType.DISTRICT_CMP_DIVISION
        )
        POINTS_MULTIPLIER = (
            DistrictPointValues.DISTRICT_CMP_MULTIPLIER.get(
                event.year, DistrictPointValues.DISTRICT_CMP_MULIPLIER_DEFAULT
            )
            if use_dcmp_multiplier
            else DistrictPointValues.STANDARD_MULTIPLIER
        )

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
        if event.year >= 2015:
            # Switched to ranking-based points for 2015 and onward
            cls._calc_rank_based_match_points(
                event, district_points, event.matches, POINTS_MULTIPLIER
            )
        else:
            cls._calc_wlt_based_match_points(
                district_points, event.matches, POINTS_MULTIPLIER
            )

        # alliance points
        if event.event_type_enum == EventType.DISTRICT_CMP and event.divisions:
            # If this is a DCMP that has divisions, there are no alliance points
            # awarded, since a team would have got them in the division already
            pass
        elif event.alliance_selections:
            selection_points = cls._alliance_selections_to_points(
                event, POINTS_MULTIPLIER, event.alliance_selections
            )
            for team, points in selection_points.items():
                district_points["points"][team]["alliance_points"] += points
        else:
            logging.info(
                "Event {} has no alliance selection district_points!".format(
                    event.key.id()
                )
            )

        # award points
        for award in event.awards:
            point_value = 0
            if event.year >= 2014:
                if award.award_type_enum not in NON_JUDGED_NON_TEAM_AWARDS:
                    if award.award_type_enum == AwardType.CHAIRMANS:
                        point_value = DistrictPointValues.CHAIRMANS.get(
                            event.year, DistrictPointValues.CHAIRMANS_DEFAULT
                        )
                    elif award.award_type_enum in {
                        AwardType.ENGINEERING_INSPIRATION,
                        AwardType.ROOKIE_ALL_STAR,
                    }:
                        point_value = DistrictPointValues.EI_AND_RAS_DEFAULT
                    else:
                        point_value = DistrictPointValues.OTHER_AWARD_DEFAULT
            else:  # Legacy awards
                if award.award_type_enum in DistrictPointValues.LEGACY_5_PT_AWARDS.get(
                    event.year, []
                ):
                    point_value = 5
                elif (
                    award.award_type_enum
                    in DistrictPointValues.LEGACY_2_PT_AWARDS.get(event.year, [])
                ):
                    point_value = 2

            # Add award points to all teams who won
            if point_value:
                for team in award.team_list:
                    team_key = none_throws(team.string_id())
                    district_points["points"][team_key]["award_points"] += (
                        point_value * POINTS_MULTIPLIER
                    )

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
        # aggregate points from first two events and district championship
        events_by_key: Dict[EventKey, Event] = {}
        team_attendance: DefaultDict[TeamKey, List[EventKey]] = defaultdict(list)
        team_totals: Dict[TeamKey, DistrictRankingTeamTotal] = defaultdict(
            lambda: DistrictRankingTeamTotal(
                event_points=[],
                point_total=0,
                rookie_bonus=0,
                tiebreakers=DistrictRankingTiebreakers(
                    total_playoff_points=0,
                    best_playoff_points=0,
                    total_alliance_points=0,
                    best_alliance_points=0,
                    total_qual_points=0,
                ),
                qual_scores=[],
                other_bonus=0,
            )
        )
        for event in events:
            events_by_key[event.key_name] = event
            event_district_points = event.district_points
            if event_district_points is not None:
                for team_key in set(event_district_points["points"].keys()).union(
                    set(event_district_points["tiebreakers"].keys())
                ):
                    team_attendance[team_key].append(event.key_name)
                    if (
                        len(team_attendance[team_key]) <= 2
                        or event.event_type_enum == EventType.DISTRICT_CMP
                        or event.event_type_enum == EventType.DISTRICT_CMP_DIVISION
                    ):
                        if team_key in event_district_points["points"]:
                            tiebreakers = DistrictRankingTiebreakers(
                                *team_totals[team_key]["tiebreakers"]
                            )

                            team_event_points: TeamAtEventDistrictPoints = (
                                event_district_points["points"][team_key]
                            )
                            team_totals[team_key]["event_points"].append(
                                (event, team_event_points)
                            )
                            team_totals[team_key]["point_total"] += team_event_points[
                                "total"
                            ]

                            # add tiebreakers in order
                            tiebreakers = DistrictRankingTiebreakers(
                                total_playoff_points=(
                                    tiebreakers.total_playoff_points
                                    + team_event_points["elim_points"]
                                ),
                                best_playoff_points=max(
                                    tiebreakers.best_playoff_points,
                                    team_event_points["elim_points"],
                                ),
                                total_alliance_points=(
                                    tiebreakers.total_alliance_points
                                    + team_event_points["alliance_points"]
                                ),
                                best_alliance_points=max(
                                    tiebreakers.best_alliance_points,
                                    team_event_points["alliance_points"],
                                ),
                                total_qual_points=(
                                    tiebreakers.total_qual_points
                                    + team_event_points["qual_points"]
                                ),
                            )
                            team_totals[team_key]["tiebreakers"] = tiebreakers

                        if (
                            team_key in event_district_points["tiebreakers"]
                        ):  # add more tiebreakers
                            team_totals[team_key]["qual_scores"] = heapq.nlargest(
                                3,
                                [
                                    *event_district_points["tiebreakers"][team_key][
                                        "highest_qual_scores"
                                    ],
                                    *team_totals[team_key]["qual_scores"],
                                ],
                            )

        # adding in rookie bonus
        # save valid team keys
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

        # Compute bonus for back to back Single-Day Events
        # Special case for 2022
        # 2 points for teams playing 2 Single-Day Events on 1 weekend,
        # provided the 2 events are the team’s first 2 events
        # See Section 11.8.1
        # https://firstfrc.blob.core.windows.net/frc2022/Manual/Sections/2022FRCGameManual-11.pdf
        if year == 2022:
            for team_key, attendance in team_attendance.items():
                event1 = (
                    events_by_key.get(attendance[0]) if len(attendance) > 0 else None
                )
                event2 = (
                    events_by_key.get(attendance[1]) if len(attendance) > 1 else None
                )

                if event1 is None or event2 is None:
                    continue

                if event1.start_date + timedelta(days=1) == event2.start_date:
                    bonus = DistrictPointValues.BACK_TO_BACK_2022_BONUS
                    team_totals[team_key]["other_bonus"] = bonus
                    team_totals[team_key]["point_total"] += bonus

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

    @classmethod
    def _get_rookie_bonus(cls, year: Year, team_rookie_year: Year) -> int:
        bonus = 0
        if team_rookie_year == year:
            bonus = 10
        elif team_rookie_year == year - 1:
            bonus = 5

        # Handle special 2022/2023 rookie accounting due to pandemic
        # See: https://www.firstinspires.org/robotics/frc/blog/2021-2022-rookie-awards-and-district-points
        if year == 2022:
            if team_rookie_year in {2021, 2022}:
                bonus = 10
            elif team_rookie_year == 2020:
                bonus = 5

        elif year == 2023:
            if team_rookie_year in {2021, 2022}:
                bonus = 5

        return bonus

    @classmethod
    def _get_alliance_number_from_teams(
        cls,
        alliance_selections: List[EventAlliance],
        teams: List[TeamKey],
    ):
        for pos in [0, 1, 2]:
            search_team = teams[pos]
            for num, alliance in enumerate(alliance_selections):
                if search_team in alliance["picks"]:
                    return num
        return None

    @classmethod
    def _calc_elim_match_points(
        cls,
        district_points: EventDistrictPoints,
        matches: List[Match],
        alliance_selections: List[EventAlliance],
        playoff_type: PlayoffType,
        POINTS_MULTIPLIER: int,
    ):
        double_elim_alliance_pts: DefaultDict[int, int] = defaultdict(int)
        double_elim_alliance_wins: DefaultDict[int, int] = defaultdict(int)
        double_elim_team_wins: DefaultDict[TeamKey, int] = defaultdict(int)
        elim_alliances: DefaultDict[TeamKey, int] = defaultdict(int)

        finals_alliance_wins: DefaultDict[int, int] = defaultdict(int)
        finals_team_wins: DefaultDict[TeamKey, int] = defaultdict(int)
        finals_team_pts: DefaultDict[TeamKey, int] = defaultdict(int)

        if playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM:
            sf_points = DistrictPointValues.DE_4_SF_WIN
        else:
            sf_points = DistrictPointValues.DE_SF_WIN

        for match in matches:
            if not match.has_been_played or match.winning_alliance == "":
                # Skip unplayed matches
                continue

            winning_alliance = cast(AllianceColor, match.winning_alliance)

            winning_alliance_number = cls._get_alliance_number_from_teams(
                alliance_selections,
                match.alliances[winning_alliance]["teams"],
            )

            if match.comp_level == CompLevel.SF:
                double_elim_alliance_wins[winning_alliance_number] += 1

                for team in match.alliances[winning_alliance]["teams"]:
                    elim_alliances[team] = winning_alliance_number
                    double_elim_team_wins[team] += 1

                double_elim_alliance_pts[winning_alliance_number] += sf_points[
                    match.set_number
                ]

            if match.comp_level == CompLevel.F:
                finals_alliance_wins[winning_alliance_number] += 1
                for team in match.alliances[winning_alliance]["teams"]:
                    elim_alliances[team] = winning_alliance_number
                    finals_team_wins[team] += 1

        for team in finals_team_wins:
            if finals_alliance_wins[elim_alliances[team]] >= 2:
                finals_team_pts[team] += int(
                    finals_team_wins[team]
                    * DistrictPointValues.F_WIN.get(
                        match.year, DistrictPointValues.F_WIN_DEFAULT
                    )
                )

        for team in elim_alliances:
            alliance = elim_alliances[team]
            alliance_wins = double_elim_alliance_wins[alliance]
            multiplier = (
                0.0
                if alliance_wins == 0
                else double_elim_team_wins[team] / alliance_wins
            )
            district_points["points"][team]["elim_points"] = int(
                (
                    math.ceil(double_elim_alliance_pts[alliance] * multiplier)
                    + finals_team_pts[team]
                )
                * POINTS_MULTIPLIER
            )

    @classmethod
    def _calc_elim_match_points_2023(
        cls,
        district_points: EventDistrictPoints,
        matches: List[Match],
        alliance_selections: List[EventAlliance],
        playoff_type: PlayoffType,
        POINTS_MULTIPLIER: int,
    ):
        # match_set_key -> alliance -> num wins
        elim_num_wins: DefaultDict[str, DefaultDict[AllianceColor, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        elim_alliance_pts: DefaultDict[int, int] = defaultdict(int)
        elim_alliance_wins: DefaultDict[int, int] = defaultdict(int)
        elim_team_wins: DefaultDict[TeamKey, int] = defaultdict(int)
        elim_alliances: DefaultDict[TeamKey, int] = defaultdict(int)

        if playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM:
            sf_points = DistrictPointValues.DE_4_SF_WIN
        else:
            sf_points = DistrictPointValues.DE_SF_WIN

        for match in matches:
            if not match.has_been_played or match.winning_alliance == "":
                # Skip unplayed matches
                continue

            match_set_key = "{}_{}{}".format(
                match.event_key_name, match.comp_level, match.set_number
            )
            winning_alliance = cast(AllianceColor, match.winning_alliance)
            elim_num_wins[match_set_key][winning_alliance] += 1

            # Get alliance numbers
            winning_alliance_number = cls._get_alliance_number_from_teams(
                alliance_selections,
                match.alliances[winning_alliance]["teams"],
            )

            elim_alliance_wins[winning_alliance_number] += 1

            for team in match.alliances[winning_alliance]["teams"]:
                elim_alliances[team] = winning_alliance_number
                elim_team_wins[team] += 1

            if match.comp_level == CompLevel.SF:
                elim_alliance_pts[winning_alliance_number] += sf_points[
                    match.set_number
                ]
            elif (
                match.comp_level == CompLevel.F
                and elim_num_wins[match_set_key][winning_alliance] >= 2
            ):
                elim_alliance_pts[winning_alliance_number] += int(
                    2
                    * DistrictPointValues.F_WIN.get(
                        match.year, DistrictPointValues.F_WIN_DEFAULT
                    )
                )

        for team in elim_alliances:
            alliance = elim_alliances[team]
            multiplier = elim_team_wins[team] / elim_alliance_wins[alliance]
            district_points["points"][team]["elim_points"] = (
                math.ceil(elim_alliance_pts[alliance] * multiplier) * POINTS_MULTIPLIER
            )

    @classmethod
    def _calc_elim_match_points_pre_2023(
        cls,
        district_points: EventDistrictPoints,
        matches: List[Match],
        POINTS_MULTIPLIER: int,
    ):
        # match_set_key -> alliance -> num wins
        elim_num_wins: DefaultDict[str, DefaultDict[AllianceColor, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # match_set_key -> alliance -> list of list of teams
        elim_alliances: DefaultDict[str, DefaultDict[AllianceColor, List[TeamKey]]] = (
            defaultdict(lambda: defaultdict(list))
        )
        for match in matches:
            if not match.has_been_played or match.winning_alliance == "":
                # Skip unplayed matches
                continue

            match_set_key = "{}_{}{}".format(
                match.event_key_name, match.comp_level, match.set_number
            )
            winning_alliance = cast(AllianceColor, match.winning_alliance)
            elim_num_wins[match_set_key][winning_alliance] += 1
            elim_alliances[match_set_key][winning_alliance] += match.alliances[
                winning_alliance
            ]["teams"]

            # Add in points for elim match wins. Probably doesn't account for backup bots well
            # 2016-03-07: Maybe this does work for backup bots? -Eugene
            if elim_num_wins[match_set_key][winning_alliance] >= 2:
                for team in elim_alliances[match_set_key][winning_alliance]:
                    point_value = 0
                    if match.comp_level == "qf":
                        point_value = (
                            DistrictPointValues.QF_WIN.get(
                                match.year, DistrictPointValues.QF_WIN_DEFAULT
                            )
                            * POINTS_MULTIPLIER
                        )
                    elif match.comp_level == "sf":
                        point_value = (
                            DistrictPointValues.SF_WIN.get(
                                match.year, DistrictPointValues.SF_WIN_DEFAULT
                            )
                            * POINTS_MULTIPLIER
                        )
                    elif match.comp_level == "f":
                        point_value = (
                            DistrictPointValues.F_WIN.get(
                                match.year, DistrictPointValues.F_WIN_DEFAULT
                            )
                            * POINTS_MULTIPLIER
                        )
                    district_points["points"][team]["elim_points"] += int(point_value)

    @classmethod
    def _calc_elim_match_points_2015(
        cls,
        district_points: EventDistrictPoints,
        matches: Dict[CompLevel, List[Match]],
        POINTS_MULTIPLIER: int,
    ) -> None:
        # count number of matches played per team per comp level
        num_played = defaultdict(lambda: defaultdict(int))
        for level in [CompLevel.QF, CompLevel.SF]:
            for match in matches[level]:
                if not match.has_been_played:
                    continue
                for color in ALLIANCE_COLORS:
                    for team in match.alliances[color]["teams"]:
                        num_played[level][team] += 1

        # qf and sf points
        advancement = PlayoffAdvancementHelper.generate_playoff_advancement_2015(
            matches
        )
        for last_level, level in [
            (CompLevel.QF, CompLevel.SF),
            (CompLevel.SF, CompLevel.F),
        ]:
            for teams, _, _, _ in advancement[last_level]:
                teams = ["frc{}".format(t) for t in teams]
                done = False
                for match in matches[level]:
                    for color in ALLIANCE_COLORS:
                        if (
                            set(teams).intersection(
                                set(match.alliances[color]["teams"])
                            )
                            != set()
                        ):
                            for team in teams:
                                points = (
                                    DistrictPointValues.QF_WIN.get(
                                        match.year, DistrictPointValues.QF_WIN_DEFAULT
                                    )
                                    if last_level == CompLevel.QF
                                    else DistrictPointValues.SF_WIN.get(
                                        match.year, DistrictPointValues.SF_WIN_DEFAULT
                                    )
                                )
                                district_points["points"][team]["elim_points"] += (
                                    int(
                                        math.ceil(points * num_played[last_level][team])
                                    )
                                    * POINTS_MULTIPLIER
                                )
                            done = True
                            break
                        if done:
                            break
                    if done:
                        break

        # final points
        num_wins = {"red": 0, "blue": 0}
        team_matches_played = {"red": [], "blue": []}
        for match in matches[CompLevel.F]:
            if not match.has_been_played or match.winning_alliance == "":
                continue

            num_wins[match.winning_alliance] += 1
            winning_alliance = cast(AllianceColor, match.winning_alliance)
            for team in match.alliances[winning_alliance]["teams"]:
                team_matches_played[match.winning_alliance].append(team)

            if num_wins[match.winning_alliance] >= 2:
                points = DistrictPointValues.F_WIN.get(
                    match.year, DistrictPointValues.F_WIN_DEFAULT
                )
                for team in team_matches_played[winning_alliance]:
                    district_points["points"][team]["elim_points"] += int(
                        points * POINTS_MULTIPLIER
                    )

    @classmethod
    def _calc_wlt_based_match_points(
        cls,
        district_points: EventDistrictPoints,
        matches: List[Match],
        POINTS_MULTIPLIER: int,
    ) -> None:
        """
        Calculates match district points based on team record (wins, losses, ties)
        This algorithm was used prior to the 2015 season
        """
        elim_matches = []
        for match in matches:
            if not match.has_been_played:
                continue

            if match.comp_level == CompLevel.QM:  # Qual match points
                if match.winning_alliance == "":  # Match is a tie
                    for team in match.team_key_names:
                        district_points["points"][team]["qual_points"] += (
                            DistrictPointValues.MATCH_TIE * POINTS_MULTIPLIER
                        )
                else:  # Somebody won the match
                    winning_alliance = cast(AllianceColor, match.winning_alliance)
                    for team in match.alliances[winning_alliance]["teams"]:
                        district_points["points"][team]["qual_points"] += (
                            DistrictPointValues.MATCH_WIN * POINTS_MULTIPLIER
                        )
                        district_points["tiebreakers"][team]["qual_wins"] += 1

                for color in ALLIANCE_COLORS:
                    for team in match.alliances[color]["teams"]:
                        score = match.alliances[color]["score"]
                        district_points["tiebreakers"][team]["highest_qual_scores"] = (
                            heapq.nlargest(
                                3,
                                district_points["tiebreakers"][team][
                                    "highest_qual_scores"
                                ]
                                + [score],
                            )
                        )
                        # Make sure that teams without wins don't get dropped from 'points'
                        district_points["points"][team]["qual_points"] += 0
            else:  # Elim match points
                elim_matches.append(match)
        cls._calc_elim_match_points_pre_2023(
            district_points, elim_matches, POINTS_MULTIPLIER
        )

    @classmethod
    def _calc_rank_based_match_points(
        cls,
        event: Event,
        district_points: EventDistrictPoints,
        matches: List[Match],
        POINTS_MULTIPLIER: int,
    ) -> None:
        """
        Calculates match district points based on team ranking
        This algorithm was introduced for the 2015 season and also used for 2016
        See: http://www.firstinspires.org/node/7616 and also
        http://www.firstinspires.org/robotics/frc/blog/Admin-Manual-Section-7-and-the-FIRST-STRONGHOLD-Logo
        """
        # qual match points are calculated by rank
        rankings = event.details.rankings2 if event.details else None
        if rankings:
            num_teams = len(rankings)
            alpha = 1.07
            for ranking in rankings:
                rank = ranking["rank"]
                team = ranking["team_key"]
                qual_points = int(
                    math.ceil(
                        cls.inverf(
                            float(num_teams - 2 * rank + 2) / (alpha * num_teams)
                        )
                        * (10.0 / cls.inverf(1.0 / alpha))
                        + 12
                    )
                )
                district_points["points"][team]["qual_points"] = (
                    qual_points * POINTS_MULTIPLIER
                )
        else:
            logging.info(
                "Event {} has no rankings for qual_points calculations!".format(
                    event.key.id()
                )
            )

        _count, organized_matches = MatchHelper.organized_matches(matches)

        # qual match calculations. only used for tiebreaking
        for match in organized_matches[CompLevel.QM]:
            for color in ALLIANCE_COLORS:
                for team in match.alliances[color]["teams"]:
                    score = match.alliances[color]["score"]
                    district_points["tiebreakers"][team]["highest_qual_scores"] = (
                        heapq.nlargest(
                            3,
                            district_points["tiebreakers"][team]["highest_qual_scores"]
                            + [score],
                        )
                    )

        # elim match point calculations
        if event.year == 2015:
            cls._calc_elim_match_points_2015(
                district_points, organized_matches, POINTS_MULTIPLIER
            )
        elif event.year <= 2022:
            elim_matches = (
                organized_matches.get(CompLevel.QF, [])
                + organized_matches.get(CompLevel.SF, [])
                + organized_matches.get(CompLevel.F, [])
            )
            cls._calc_elim_match_points_pre_2023(
                district_points, elim_matches, POINTS_MULTIPLIER
            )
        else:
            elim_alliances = event.alliance_selections
            if elim_alliances is not None:
                elim_matches = organized_matches.get(
                    CompLevel.SF, []
                ) + organized_matches.get(CompLevel.F, [])
                if event.year == 2023:
                    cls._calc_elim_match_points_2023(
                        district_points,
                        elim_matches,
                        elim_alliances,
                        event.playoff_type,
                        POINTS_MULTIPLIER,
                    )
                else:
                    cls._calc_elim_match_points(
                        district_points,
                        elim_matches,
                        elim_alliances,
                        event.playoff_type,
                        POINTS_MULTIPLIER,
                    )

    @classmethod
    def _alliance_selections_to_points(
        self, event: Event, multiplier: int, alliance_selections: List[EventAlliance]
    ) -> Dict[TeamKey, int]:
        team_points: Dict[TeamKey, int] = {}
        try:
            if event.key.id() == "2015micmp":
                # Special case for 2015 Michigan District CMP, due to there being 16 alliances instead of 8
                # Uses max of 48 points and no multiplier
                # See 2015 Admin Manual, section 7.4.3.1
                # http://www.firstinspires.org/sites/default/files/uploads/resource_library/frc/game-and-season-info/archive/2015/AdminManual20150407.pdf
                for n, alliance in enumerate(alliance_selections):
                    team_points[alliance["picks"][0]] = int(48 - (1.5 * n))
                    team_points[alliance["picks"][1]] = int(48 - (1.5 * n))
                    team_points[alliance["picks"][2]] = int((n + 1) * 1.5)
                    n += 1
            elif (
                event.year == 2022
                and event.event_type_enum == EventType.DISTRICT
                and event.playoff_type == PlayoffType.BRACKET_4_TEAM
            ):
                # 2022 single day district event modifications:
                # For Single-Day Events, ALLIANCE CAPTAINS #1, 2, 3, and 4 receive 16, 14, 12, and 10 points respectively.
                # For Single-Day Events, first through eighth picks receive 16, 14, 12, 10, 8, 6, 4, and 2 points respectively.
                # See Section 11.8.1
                # https://firstfrc.blob.core.windows.net/frc2022/Manual/Sections/2022FRCGameManual-11.pdf
                for n, alliance in enumerate(alliance_selections):
                    team_points[alliance["picks"][0]] = int(16 - (2 * n))
                    team_points[alliance["picks"][1]] = int(16 - (2 * n))
                    team_points[alliance["picks"][2]] = int(2 + (2 * n))
                    n += 1
            else:
                for n, alliance in enumerate(alliance_selections):
                    n += 1
                    team_points[alliance["picks"][0]] = (17 - n) * multiplier
                    team_points[alliance["picks"][1]] = (17 - n) * multiplier
                    team_points[alliance["picks"][2]] = n * multiplier
        except Exception:
            # Log only if this matters
            if event.district_key is not None:
                logging.exception(
                    "Alliance points calc for {} errored!".format(event.key.id())
                )

        return team_points
