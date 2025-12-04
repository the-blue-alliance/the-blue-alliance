import datetime
import json
from collections.abc import Mapping, MutableSequence, Sequence
from typing import Any, TypedDict

from pyre_extensions import safe_json

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.comp_level import COMP_LEVELS, CompLevel
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.score_breakdown_keys import ScoreBreakdownKeys
from backend.common.models.alliance import MatchAlliance
from backend.common.models.keys import TeamKey, Year
from backend.common.models.team import Team


def _parse_datetime(value: str | None, field_name: str) -> datetime.datetime | None:
    if value is None:
        return None
    try:
        dt = datetime.datetime.fromisoformat(value)
        # remove timezone info because DatetimeProperty can't handle timezones
        return dt.replace(tzinfo=None)
    except ValueError:
        raise ParserInputException(
            f"Could not parse '{field_name}'. Check that it is in ISO 8601 format."
        )


class MatchInput(TypedDict, total=False):
    comp_level: CompLevel
    set_number: int
    match_number: int
    alliances: Mapping[AllianceColor, MatchAlliance]
    score_breakdowns: Mapping[AllianceColor, dict[str, Any]]
    time_string: str
    time: str
    display_name: str


class ParsedMatch(TypedDict):
    comp_level: CompLevel
    set_number: int
    match_number: int
    alliances_json: str
    score_breakdown_json: str | None
    time_string: str | None
    time: datetime.datetime | None
    actual_start_time: datetime.datetime | None
    post_results_time: datetime.datetime | None
    team_key_names: Sequence[TeamKey]
    display_name: str | None


class JSONMatchesParser:
    @staticmethod
    def parse[T: (str, bytes)](matches_json: T, year: Year) -> Sequence[ParsedMatch]:
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
            if not isinstance(match, dict):
                raise ParserInputException("Matches must be dicts.")

            comp_level = match.get("comp_level")
            set_number = match.get("set_number")
            match_number = match.get("match_number")
            alliances = match.get("alliances")
            score_breakdown = match.get("score_breakdown")
            time_string = match.get("time_string")
            time_utc = match.get("time_utc")
            actual_start_time_utc = match.get("actual_start_time_utc")
            post_results_time_utc = match.get("post_results_time_utc")
            display_name = match.get("display_name")

            if comp_level is None:
                raise ParserInputException("Match must have a 'comp_level'")
            if comp_level not in COMP_LEVELS:
                raise ParserInputException(
                    "'comp_level' must be one of: {}".format(COMP_LEVELS)
                )

            if comp_level == CompLevel.QM:
                set_number = 1
            elif set_number is None or type(set_number) is not int:
                raise ParserInputException("Match must have an integer 'set_number'")

            if match_number is None or type(match_number) is not int:
                raise ParserInputException("Match must have an integer 'match_number'")

            if not isinstance(alliances, dict):
                raise ParserInputException("'alliances' must be a dict")

            for color, details in alliances.items():
                if color not in ALLIANCE_COLORS:
                    raise ParserInputException(
                        f"Alliance color '{color}' not recognized"
                    )
                for key in ("teams", "score"):
                    if key not in details:
                        raise ParserInputException(
                            f"alliances[{color}] must have key '{key}'"
                        )
                for team_key in details["teams"]:
                    if not Team.validate_key_name(str(team_key)):
                        raise ParserInputException(
                            f"Bad team: '{team_key}'. Must follow format 'frcXXX'."
                        )

                if details["score"] is not None and type(details["score"]) is not int:
                    raise ParserInputException(
                        f"alliances[{color}]['score'] must be an integer or null"
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
                if not isinstance(score_breakdown, dict):
                    raise ParserInputException("'score_breakdown' must be a dict")

                for color, breakdown in score_breakdown.items():
                    if color not in ALLIANCE_COLORS:
                        raise ParserInputException(
                            f"Alliance color '{color}' not recognized"
                        )
                    if invalid_keys := set(breakdown.keys()) - VALID_BREAKDOWN_KEYS:
                        raise ParserInputException(
                            f"Invalid score breakdown fields for {year}: {sorted(invalid_keys)}. "
                            f"Valid keys are: {sorted(VALID_BREAKDOWN_KEYS)}"
                        )

            datetime_utc = _parse_datetime(time_utc, "time_utc")
            actual_start_time_utc = _parse_datetime(
                actual_start_time_utc, "actual_start_time_utc"
            )
            post_results_time_utc = _parse_datetime(
                post_results_time_utc, "post_results_time_utc"
            )

            if display_name is not None and type(display_name) is not str:
                raise ParserInputException("'display_name' must be a string")

            # validation passed. build new dicts to sanitize
            parsed_alliances: dict[AllianceColor, MatchAlliance] = {
                color: MatchAlliance(
                    teams=alliance_data["teams"],
                    score=alliance_data["score"],
                    surrogates=alliance_data.get("surrogates", []),
                    dqs=alliance_data.get("dqs", []),
                )
                for color in AllianceColor
                if (alliance_data := alliances.get(color)) is not None
            }

            team_key_names: list[TeamKey] = [
                team
                for alliance in parsed_alliances.values()
                for team in alliance["teams"]
            ]

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
                "team_key_names": team_key_names,
                "display_name": display_name,
            }

            parsed_matches.append(parsed_match)

        return parsed_matches
