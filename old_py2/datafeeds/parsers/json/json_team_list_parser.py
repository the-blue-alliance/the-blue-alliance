import json
import re

from datafeeds.parser_base import ParserInputException, ParserBase


class JSONTeamListParser(ParserBase):
    @classmethod
    def parse(self, team_list_json):
        """
        Parse JSON that contains team_keys in the format "frcXXX"
        Format is as follows:
        [team1, team1, team3, ...]
        """
        try:
            team_keys = json.loads(team_list_json)
        except:
            raise ParserInputException("Invalid JSON. Please check input.")

        for team_key in team_keys:
            if not re.match(r'frc\d+', str(team_key)):
                raise ParserInputException("Bad team_key: '{}'. Must follow format 'frcXXX' or be null.".format(team_key))

        return team_keys
