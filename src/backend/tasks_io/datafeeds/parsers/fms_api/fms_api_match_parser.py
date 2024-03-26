import datetime
import json
import logging
from typing import Any, Dict, List, Tuple

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.media_type import MediaType
from backend.common.consts.playoff_type import DOUBLE_ELIM_TYPES
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.playoff_type_helper import PlayoffTypeHelper
from backend.common.models.event import Event
from backend.common.models.keys import MatchKey, TeamKey, Year
from backend.common.models.match import Match
from backend.common.models.match_score_breakdown import MatchScoreBreakdown
from backend.common.suggestions.media_parser import MediaParser
from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON

QF_SF_MAP = {
    1: (1, 3),  # in sf1, qf seeds 2 and 4 play. 0-indexed becomes 1, 3
    2: (0, 2),
    3: (1, 2),
    4: (0, 3),
    5: (2, 3),
    6: (0, 1),
}

LAST_LEVEL = {CompLevel.SF: CompLevel.QF, CompLevel.F: CompLevel.SF}

TIME_PATTERN = "%Y-%m-%dT%H:%M:%S"


class FMSAPIHybridScheduleParser(
    ParserJSON[Tuple[List[Match], Dict[MatchKey, MatchKey]]]
):
    def __init__(self, year: Year, event_short: str):
        self.year = year
        self.event_short = event_short

    @classmethod
    def is_blank_match(cls, match: Match) -> bool:
        """
        Detect junk playoff matches like in 2017scmb
        """
        if match.comp_level == CompLevel.QM or not match.score_breakdown:
            return False
        for color in ALLIANCE_COLORS:
            if match.alliances[color]["score"] != 0:
                return False
            for value in none_throws(match.score_breakdown)[color].values():
                if value and value not in {
                    "Unknown",
                    "None",
                }:  # Nonzero, False, blank, None, etc.
                    return False
        return True

    def parse(
        self, response: Dict[str, Any]
    ) -> Tuple[List[Match], Dict[MatchKey, MatchKey]]:
        import pytz

        matches = response["Schedule"]

        event_key = f"{self.year}{self.event_short}"
        event = none_throws(Event.get_by_id(event_key))
        if event.timezone_id:
            event_tz = pytz.timezone(event.timezone_id)
        else:
            logging.warning(
                "Event {} has no timezone! Match times may be wrong.".format(event_key)
            )
            event_tz = None

        match_identifiers: List[Tuple[MatchKey, CompLevel, int, int]] = []
        for match in matches:
            if "tournamentLevel" in match:  # 2016+
                level = match["tournamentLevel"]
            else:  # 2015
                level = match["level"]
            comp_level = PlayoffTypeHelper.get_comp_level(
                event.playoff_type, level, match["matchNumber"]
            )
            set_number, match_number = PlayoffTypeHelper.get_set_match_number(
                event.playoff_type, comp_level, match["matchNumber"]
            )
            key_name = Match.render_key_name(
                event_key, comp_level.value, set_number, match_number
            )
            match_identifiers.append((key_name, comp_level, set_number, match_number))

        # Prefetch matches for tiebreaker checking
        ndb.get_multi_async(
            [ndb.Key(Match, key_name) for (key_name, _, _, _) in match_identifiers]
        )

        parsed_matches: List[Match] = []
        remapped_matches: Dict[
            MatchKey, MatchKey
        ] = {}  # If a key changes due to a tiebreaker
        for match, (key_name, comp_level, set_number, match_number) in zip(
            matches, match_identifiers
        ):
            red_teams: List[TeamKey] = []
            blue_teams: List[TeamKey] = []
            red_surrogates: List[TeamKey] = []
            blue_surrogates: List[TeamKey] = []
            red_dqs: List[TeamKey] = []
            blue_dqs: List[TeamKey] = []
            team_key_names: List[TeamKey] = []

            # Sort by station to ensure correct ordering. Kind of hacky.
            sorted_teams = list(
                sorted(
                    match.get("teams", match.get("Teams", [])),
                    key=lambda team: team["station"],
                )
            )

            null_team = any(t["teamNumber"] is None for t in sorted_teams)
            if (
                null_team
                and match["scoreRedFinal"] is None
                and match["scoreBlueFinal"] is None
            ):
                continue

            for team in sorted_teams:
                if team["teamNumber"] is None:
                    continue

                team_key = "frc{}".format(team["teamNumber"])
                team_key_names.append(team_key)
                if "Red" in team["station"]:
                    red_teams.append(team_key)
                    if team.get("surrogate", None):
                        red_surrogates.append(team_key)
                    if team.get("dq", None):
                        red_dqs.append(team_key)
                elif "Blue" in team["station"]:
                    blue_teams.append(team_key)
                    if team.get("surrogate", None):
                        blue_surrogates.append(team_key)
                    if team.get("dq", None):
                        blue_dqs.append(team_key)

            alliances = {
                "red": {
                    "teams": red_teams,
                    "surrogates": red_surrogates,
                    "dqs": red_dqs,
                    "score": match["scoreRedFinal"],
                },
                "blue": {
                    "teams": blue_teams,
                    "surrogates": blue_surrogates,
                    "dqs": blue_dqs,
                    "score": match["scoreBlueFinal"],
                },
            }

            if not match[
                "startTime"
            ]:  # no startTime means it's an unneeded rubber match
                continue

            time = datetime.datetime.strptime(
                match["startTime"].split(".")[0], TIME_PATTERN
            )
            if event_tz is not None:
                time = time - event_tz.utcoffset(time)

            actual_time_raw = (
                match["actualStartTime"] if "actualStartTime" in match else None
            )
            actual_time = None
            if actual_time_raw is not None:
                actual_time = datetime.datetime.strptime(
                    actual_time_raw.split(".")[0], TIME_PATTERN
                )
                if event_tz is not None:
                    actual_time = actual_time - event_tz.utcoffset(actual_time)

            post_result_time_raw = match.get("postResultTime")
            post_result_time = None
            if post_result_time_raw is not None:
                post_result_time = datetime.datetime.strptime(
                    post_result_time_raw.split(".")[0], TIME_PATTERN
                )
                if event_tz is not None:
                    post_result_time = post_result_time - event_tz.utcoffset(
                        post_result_time
                    )

            youtube_videos = []
            video_link = match.get("matchVideoLink")
            if video_link:
                video_suggestion = MediaParser.partial_media_dict_from_url(video_link)
                if (
                    video_suggestion
                    and video_suggestion["media_type_enum"] == MediaType.YOUTUBE_VIDEO
                ):
                    youtube_videos.append(video_suggestion["foreign_key"])

            # Check for tiebreaker matches
            existing_match = Match.get_by_id(
                key_name
            )  # Should be in instance cache due to prefetching above
            # Follow chain of existing matches
            while (
                existing_match is not None
                and existing_match.tiebreak_match_key is not None
            ):
                logging.info(
                    "Following Match {} to {}".format(
                        existing_match.key.id(), existing_match.tiebreak_match_key.id()
                    )
                )
                existing_match = existing_match.tiebreak_match_key.get()
            # Check if last existing match needs to be tiebroken
            if (
                existing_match
                and existing_match.comp_level != "qm"
                and existing_match.has_been_played
                and existing_match.winning_alliance == ""
                and existing_match.actual_time != actual_time
                and not self.is_blank_match(existing_match)
            ):
                logging.info("Match {} is tied!".format(existing_match.key.id()))

                # TODO: Only query within set if set_number ever gets indexed
                match_count = 0
                for match_key in Match.query(
                    Match.event == event.key, Match.comp_level == comp_level
                ).fetch(keys_only=True):
                    _, match_key = match_key.id().split("_")
                    if match_key.startswith("{}{}".format(comp_level, set_number)):
                        match_count += 1

                # Sanity check:
                # In a classic bracket, tiebreakers must be played after at least 3 matches
                # if not finals
                # But in a double elim bracket, we can play them immediately
                if (
                    event.playoff_type not in DOUBLE_ELIM_TYPES
                    and match_count < 3
                    and comp_level != CompLevel.F
                ):
                    logging.warning(
                        "Match supposedly tied, but existing count is {}! Skipping match.".format(
                            match_count
                        )
                    )
                    continue

                match_number = match_count + 1
                new_key_name = Match.render_key_name(
                    event_key, comp_level.value, set_number, match_number
                )
                remapped_matches[key_name] = new_key_name
                key_name = new_key_name

                # Point existing match to new tiebreaker match
                existing_match.tiebreak_match_key = ndb.Key(Match, key_name)
                parsed_matches.append(existing_match)

                logging.info("Creating new match: {}".format(key_name))
            elif existing_match:
                remapped_matches[key_name] = existing_match.key.id()
                key_name = existing_match.key.id()
                match_number = existing_match.match_number

            parsed_matches.append(
                Match(
                    id=key_name,
                    event=event.key,
                    year=event.year,
                    set_number=set_number,
                    match_number=match_number,
                    comp_level=comp_level,
                    team_key_names=team_key_names,
                    time=time,
                    actual_time=actual_time,
                    post_result_time=post_result_time,
                    alliances_json=json.dumps(alliances),
                    youtube_videos=youtube_videos,
                )
            )

        if self.year == 2015:
            # Fix null teams in elims (due to FMS API failure, some info not complete)
            # Should only happen for sf and f matches
            _, organized_matches = MatchHelper.organized_matches(parsed_matches)
            for level in [CompLevel.SF, CompLevel.F]:
                playoff_advancement = (
                    PlayoffAdvancementHelper.generate_playoff_advancement_2015(
                        organized_matches
                    )
                )
                if playoff_advancement[LAST_LEVEL[level]] != []:
                    for match in organized_matches[level]:
                        if "frcNone" in match.team_key_names:
                            if level == "sf":
                                red_seed, blue_seed = QF_SF_MAP[match.match_number]
                            else:
                                red_seed = 0
                                blue_seed = 1
                            red_teams = [
                                "frc{}".format(t)
                                for t in playoff_advancement[LAST_LEVEL[level]][
                                    red_seed
                                ][0]
                            ]
                            blue_teams = [
                                "frc{}".format(t)
                                for t in playoff_advancement[LAST_LEVEL[level]][
                                    blue_seed
                                ][0]
                            ]

                            alliances = match.alliances
                            alliances[AllianceColor.RED]["teams"] = red_teams
                            alliances[AllianceColor.BLUE]["teams"] = blue_teams
                            match.alliances_json = json.dumps(alliances)
                            match.team_key_names = red_teams + blue_teams

            fixed_matches = []
            for key, matches in organized_matches.items():
                if key != "num":
                    for match in matches:
                        if "frcNone" not in match.team_key_names:
                            fixed_matches.append(match)
            parsed_matches = fixed_matches

        return parsed_matches, remapped_matches


class FMSAPIMatchDetailsParser(ParserJSON[Dict[MatchKey, MatchScoreBreakdown]]):
    def __init__(self, year, event_short):
        self.year = year
        self.event_short = event_short

    def parse(self, response: Dict[str, Any]) -> Dict[MatchKey, MatchScoreBreakdown]:
        matches = response["MatchScores"]

        event_key = "{}{}".format(self.year, self.event_short)
        event = none_throws(Event.get_by_id(event_key))

        match_details_by_key: Dict[MatchKey, MatchScoreBreakdown] = {}

        for match in matches:
            comp_level = PlayoffTypeHelper.get_comp_level(
                event.playoff_type, match["matchLevel"], match["matchNumber"]
            )
            set_number, match_number = PlayoffTypeHelper.get_set_match_number(
                event.playoff_type, comp_level, match["matchNumber"]
            )
            breakdown: MatchScoreBreakdown = {
                AllianceColor.RED: {},
                AllianceColor.BLUE: {},
            }
            # TODO better type hinting for per-year breakdowns
            if "coopertition" in match:
                breakdown["coopertition"] = match["coopertition"]  # pyre-ignore[6]
            if "coopertitionPoints" in match:
                breakdown["coopertition_points"] = match[  # pyre-ignore[6]
                    "coopertitionPoints"
                ]

            game_data = None
            if self.year == 2018:
                # Switches should be the same, but parse individually in case FIRST change things
                right_switch_red = match["switchRightNearColor"] == "Red"
                scale_red = match["scaleNearColor"] == "Red"
                left_switch_red = match["switchLeftNearColor"] == "Red"
                game_data = "{}{}{}".format(
                    "L" if right_switch_red else "R",
                    "L" if scale_red else "R",
                    "L" if left_switch_red else "R",
                )

            elif self.year == 2024:
                # Bonus thresholds and coop status are in the top level Match object,
                # duplicate them into each alliance breakdown
                for key in [
                    "coopertitionBonusAchieved",
                    "melodyBonusThresholdCoop",
                    "melodyBonusThresholdNonCoop",
                    "melodyBonusThreshold",
                    "ensembleBonusStagePointsThreshold",
                    "ensembleBonusOnStageRobotsThreshold",
                ]:
                    for color in ALLIANCE_COLORS:
                        breakdown[color][key] = match[key]

            for alliance in match.get("alliances", match.get("Alliances", [])):
                color = alliance["alliance"].lower()
                for key, value in alliance.items():
                    if key != "alliance":
                        breakdown[color][key] = value

                if game_data is not None:
                    breakdown[color]["tba_gameData"] = game_data

                if self.year == 2019:
                    # Derive incorrect completedRocketFar and completedRocketNear returns from FIRST API
                    for side1 in ["Near", "Far"]:
                        completedRocket = True
                        for side2 in ["Left", "Right"]:
                            for level in ["low", "mid", "top"]:
                                if (
                                    breakdown[color][
                                        "{}{}Rocket{}".format(level, side2, side1)
                                    ]
                                    != "PanelAndCargo"
                                ):
                                    completedRocket = False
                                    break
                            if not completedRocket:
                                break
                        breakdown[color][
                            "completedRocket{}".format(side1)
                        ] = completedRocket

            match_details_by_key[
                Match.render_key_name(
                    "{}{}".format(self.year, self.event_short),
                    comp_level.value,
                    set_number,
                    match_number,
                )
            ] = breakdown

        return match_details_by_key
