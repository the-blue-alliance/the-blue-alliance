import json
import re

from datafeeds.parser_base import ParserInputException, ParserBase
from helpers.match_helper import MatchHelper
from models.match import Match


class JSONMatchesParser(ParserBase):
    @classmethod
    def parse(self, matches_json, year):
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
        try:
            matches = json.loads(matches_json)
        except:
            raise ParserInputException("Invalid JSON. Please check input.")

        parsed_matches = []
        for match in matches:
            if type(match) is not dict:
                raise ParserInputException("Matches must be dicts.")

            comp_level = match.get('comp_level', None)
            set_number = match.get('set_number', None)
            match_number = match.get('match_number', None)
            alliances = match.get('alliances', None)
            score_breakdown = match.get('score_breakdown', None)
            time_string = match.get('time_string', None)
            time_utc = match.get('time_utc', None)

            if comp_level is None:
                raise ParserInputException("Match must have a 'comp_level'")
            if comp_level not in Match.COMP_LEVELS:
                raise ParserInputException("'comp_level' must be one of: {}".format(Match.COMP_LEVELS))

            if comp_level == 'qm':
                set_number = 1
            elif set_number is None or type(set_number) is not int:
                raise ParserInputException("Match must have an integer 'set_number'")

            if match_number is None or type(match_number) is not int:
                raise ParserInputException("Match must have an integer 'match_number'")

            if type(alliances) is not dict:
                raise ParserInputException("'alliances' must be a dict")
            else:
                for color, details in alliances.items():
                    if color not in {'red', 'blue'}:
                        raise ParserInputException("Alliance color '{}' not recognized".format(color))
                    if 'teams' not in details:
                        raise ParserInputException("alliances[color] must have key 'teams'")
                    if 'score' not in details:
                        raise ParserInputException("alliances[color] must have key 'score'")
                    for team_key in details['teams']:
                        if not re.match(r'frc\d+', str(team_key)):
                            raise ParserInputException("Bad team: '{}'. Must follow format 'frcXXX'.".format(team_key))
                    if details['score'] is not None and type(details['score']) is not int:
                        raise ParserInputException("alliances[color]['score'] must be an integer or null")

                    for team_key in details.get('surrogates', []):
                        if not re.match(r'frc\d+', str(team_key)):
                            raise ParserInputException("Bad surrogate team: '{}'. Must follow format 'frcXXX'.".format(team_key))
                        if team_key not in details['teams']:
                            raise ParserInputException("Bad surrogate team: '{}'. Must be a team in the match.'.".format(team_key))
                    for team_key in details.get('dqs', []):
                        if not re.match(r'frc\d+', str(team_key)):
                            raise ParserInputException("Bad dq team: '{}'. Must follow format 'frcXXX'.".format(team_key))
                        if team_key not in details['teams']:
                            raise ParserInputException("Bad dq team: '{}'. Must be a team in the match.'.".format(team_key))

            if score_breakdown is not None:
                if type(score_breakdown) is not dict:
                    raise ParserInputException("'score_breakdown' must be a dict")
                else:
                    for color, breakdown in score_breakdown.items():
                        if color not in {'red', 'blue'}:
                            raise ParserInputException("Alliance color '{}' not recognized".format(color))
                        for k in breakdown.keys():
                            is_valid = MatchHelper.is_valid_score_breakdown_key(k, year)
                            if is_valid != True:
                                raise ParserInputException("Valid score breakdowns for {} are: {}".format(year, is_valid))

            datetime_utc = None
            if time_utc is not None:
                try:
                    import iso8601
                    datetime_utc = iso8601.parse_date(time_utc)
                    # remove timezone info because DatetimeProperty can't handle timezones
                    datetime_utc = datetime_utc.replace(tzinfo=None)
                except Exception:
                    raise ParserInputException("Could not parse 'time_utc'. Check that it is in ISO 8601 format.")

            # validation passed. build new dicts to sanitize
            parsed_alliances = {
                'red': {
                    'teams': alliances['red']['teams'],
                    'score': alliances['red']['score'],
                    'surrogates': alliances['red'].get('surrogates', []),
                    'dqs': alliances['red'].get('dqs', []),
                },
                'blue': {
                    'teams': alliances['blue']['teams'],
                    'score': alliances['blue']['score'],
                    'surrogates': alliances['blue'].get('surrogates', []),
                    'dqs': alliances['blue'].get('dqs', []),
                },
            }
            parsed_match = {
                'comp_level': comp_level,
                'set_number': set_number,
                'match_number': match_number,
                'alliances_json': json.dumps(parsed_alliances),
                'score_breakdown_json': json.dumps(score_breakdown) if score_breakdown is not None else None,
                'time_string': time_string,
                'time': datetime_utc,
                'team_key_names': parsed_alliances['red']['teams'] + parsed_alliances['blue']['teams'],
            }

            parsed_matches.append(parsed_match)
        return parsed_matches
