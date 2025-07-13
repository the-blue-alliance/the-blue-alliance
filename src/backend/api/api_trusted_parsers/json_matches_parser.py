import datetime
import json
from typing import (
    Any,
    AnyStr,
    Dict,
    Mapping,
    MutableSequence,
    Optional,
    Sequence,
    TypedDict,
)

from pyre_extensions import safe_json

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import COMP_LEVELS, CompLevel
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.score_breakdown_keys import ScoreBreakdownKeys
from backend.common.models.alliance import MatchAlliance
from backend.common.models.keys import TeamKey, Year
from backend.common.models.team import Team


class MatchInput(TypedDict, total=False):
    comp_level: CompLevel
    set_number: int
    match_number: int
    alliances: Mapping[AllianceColor, MatchAlliance]
    score_breakdowns: Mapping[AllianceColor, Dict[str, Any]]
    time_string: str
    time: str
    display_name: str


class ParsedMatch(TypedDict):
    comp_level: CompLevel
    set_number: int
    match_number: int
    alliances_json: str
    score_breakdown_json: Optional[str]
    time_string: str
    time: datetime.datetime
    actual_start_time: Optional[datetime.datetime]
    post_results_time: Optional[datetime.datetime]
    team_key_names: Sequence[TeamKey]
    display_name: Optional[str]


class JSONMatchesParser:
    @staticmethod
    def parse(matches_json: AnyStr, year: Year) -> Sequence[ParsedMatch]:
        """
        Parse JSON that contains a list of matches for a given year where each match is a dict of:
        comp_level: String in the set {"qm", "ef", "qf", "sf", "f"}
        set_number: Integer identifying the elim set number. Ignored for qual matches. ex: the 4 in qf4m2
        match_number: Integer identifying the match number within a set. ex: the 2 in qf4m2
        alliances: Dict of {'red': {'teams': ['frcXXX'...], 'score': S, 'surrogates': ['frcXXX'...], 'dqs': ['frcXXX'...]}, 'blue': {...}}. Where scores (S) are integers. Null scores indicate that a match has not yet been played. surrogates and dqs are optional.
        score_breakdown: Dict of {'red': {K1: V1, K2: V2, ...}, 'blue': {...}}. Where Kn are keys and Vn are values for those keys.
        time_string: String in the format "(H)H:MM AM/PM" for when the match will be played in the event's local timezone. ex: "9:15 AM"
        time: UTC time of the match as a string in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        """
        VALID_BREAKDOWN_KEYS: set[str] = (
            ScoreBreakdownKeys.get_valid_score_breakdown_keys(year)
        )
        matches: Sequence[MatchInput] = safe_json.loads(
            matches_json, Sequence, validate=False
        )
        if not isinstance(matches, list):
            raise ParserInputException("Invalid JSON. Please check input.")

        parsed_matches: MutableSequence[ParsedMatch] = []
        for match in matches:
            if type(match) is not dict:
                raise ParserInputException("Matches must be dicts.")

            comp_level = match.get("comp_level", None)
            set_number = match.get("set_number", None)
            match_number = match.get("match_number", None)
            alliances = match.get("alliances", None)
            score_breakdown = match.get("score_breakdown", None)
            time_string = match.get("time_string", None)
            time_utc = match.get("time_utc", None)
            actual_start_time_utc = match.get("actual_start_time_utc", None)
            post_results_time_utc = match.get("post_results_time_utc", None)
            display_name = match.get("display_name", None)

            if comp_level is None:
                raise ParserInputException("Match must have a 'comp_level'")
            if comp_level not in COMP_LEVELS:
                raise ParserInputException(
                    "'comp_level' must be one of: {}".format(COMP_LEVELS)
                )

            if comp_level == "qm":
                set_number = 1
            elif set_number is None or type(set_number) is not int:
                raise ParserInputException("Match must have an integer 'set_number'")

            if match_number is None or type(match_number) is not int:
                raise ParserInputException("Match must have an integer 'match_number'")

            if type(alliances) is not dict:
                raise ParserInputException("'alliances' must be a dict")
            else:
                for color, details in alliances.items():
                    if color not in {"red", "blue"}:
                        raise ParserInputException(
                            "Alliance color '{}' not recognized".format(color)
                        )
                    if "teams" not in details:
                        raise ParserInputException(
                            f"alliances[{str(color)}] must have key 'teams'"
                        )
                    if "score" not in details:
                        raise ParserInputException(
                            f"alliances[{str(color)}] must have key 'score'"
                        )
                    for team_key in details["teams"]:
                        if not Team.validate_key_name(str(team_key)):
                            raise ParserInputException(
                                f"Bad team: '{team_key}'. Must follow format 'frcXXX'."
                            )
                    if (
                        details["score"] is not None
                        and type(details["score"]) is not int
                    ):
                        raise ParserInputException(
                            f"alliances[{str(color)}]['score'] must be an integer or null"
                        )

                    for team_key in details.get("surrogates", []):
                        if not Team.validate_key_name(str(team_key)):
                            raise ParserInputException(
                                f"Bad surrogate team: '{team_key}'. Must follow format 'frcXXX'."
                            )
                        if team_key not in details["teams"]:
                            raise ParserInputException(
                                f"Bad surrogate team: '{team_key}'. Must be a team in the match.'."
                            )
                    for team_key in details.get("dqs", []):
                        if not Team.validate_key_name(str(team_key)):
                            raise ParserInputException(
                                f"Bad dq team: '{team_key}'. Must follow format 'frcXXX'."
                            )
                        if team_key not in details["teams"]:
                            raise ParserInputException(
                                f"Bad dq team: '{team_key}'. Must be a team in the match.'."
                            )

            if score_breakdown is not None:
                if type(score_breakdown) is not dict:
                    raise ParserInputException("'score_breakdown' must be a dict")
                else:
                    for color, breakdown in score_breakdown.items():
                        if color not in {"red", "blue"}:
                            raise ParserInputException(
                                f"Alliance color '{color}' not recognized"
                            )
                        invalid_breakdown_keys: set[str] = (
                            set(breakdown.keys()) - VALID_BREAKDOWN_KEYS
                        )
                        if invalid_breakdown_keys:
                            raise ParserInputException(
                                f"Invalid score breakdown fields for {year}: {sorted(list(invalid_breakdown_keys))}. "
                                f"Valid keys are: {sorted(list(VALID_BREAKDOWN_KEYS))}"
                            )

            datetime_utc = None
            if time_utc is not None:
                try:
                    datetime_utc = datetime.datetime.fromisoformat(time_utc)
                    # remove timezone info because DatetimeProperty can't handle timezones
                    datetime_utc = datetime_utc.replace(tzinfo=None)
                except ValueError:
                    raise ParserInputException(
                        "Could not parse 'time_utc'. Check that it is in ISO 8601 format."
                    )

            if actual_start_time_utc is not None:
                try:
                    actual_start_time_utc = datetime.datetime.fromisoformat(
                        actual_start_time_utc
                    )
                    # remove timezone info because DatetimeProperty can't handle timezones
                    actual_start_time_utc = actual_start_time_utc.replace(tzinfo=None)
                except ValueError:
                    raise ParserInputException(
                        "Could not parse 'actual_start_time_utc'. Check that it is in ISO 8601 format."
                    )

            if post_results_time_utc is not None:
                try:
                    post_results_time_utc = datetime.datetime.fromisoformat(
                        post_results_time_utc
                    )
                    # remove timezone info because DatetimeProperty can't handle timezones
                    post_results_time_utc = post_results_time_utc.replace(tzinfo=None)
                except ValueError:
                    raise ParserInputException(
                        "Could not parse 'post_results_time_utc'. Check that it is in ISO 8601 format."
                    )

            if display_name is not None and type(display_name) is not str:
                raise ParserInputException("'display_name' must be a string")

            # validation passed. build new dicts to sanitize
            parsed_alliances: Dict[AllianceColor, MatchAlliance] = {
                AllianceColor.RED: {
                    "teams": alliances["red"]["teams"],
                    "score": alliances["red"]["score"],
                    "surrogates": alliances["red"].get("surrogates", []),
                    "dqs": alliances["red"].get("dqs", []),
                },
                AllianceColor.BLUE: {
                    "teams": alliances["blue"]["teams"],
                    "score": alliances["blue"]["score"],
                    "surrogates": alliances["blue"].get("surrogates", []),
                    "dqs": alliances["blue"].get("dqs", []),
                },
            }
            parsed_match: ParsedMatch = {
                "comp_level": comp_level,
                "set_number": set_number,
                "match_number": match_number,
                "alliances_json": json.dumps(parsed_alliances),
                "score_breakdown_json": (
                    json.dumps(score_breakdown) if score_breakdown is not None else None
                ),
                "time_string": time_string,
                "time": datetime_utc,
                "actual_start_time": actual_start_time_utc,
                "post_results_time": post_results_time_utc,
                "team_key_names": parsed_alliances[AllianceColor.RED]["teams"]
                + parsed_alliances[AllianceColor.BLUE]["teams"],
                "display_name": display_name,
            }

            parsed_matches.append(parsed_match)
        return parsed_matches
