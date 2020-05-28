import json
import re

from datafeeds.parser_base import ParserInputException, ParserBase


class JSONAllianceSelectionsParser(ParserBase):
    @classmethod
    def parse(self, alliances_json):
        """
        Parse JSON that contains team_keys
        Format is as follows:
        [[captain1, pick1-1, pick1-2(, ...)],
        ['frc254', 'frc971', 'frc604'],
        ...
        [captain8, pick8-1, pick8-2(, ...)]]
        """
        try:
            alliances = json.loads(alliances_json)
        except:
            raise ParserInputException("Invalid JSON. Please check input.")

        alliance_selections = []
        for alliance in alliances:
            is_empty = True
            selection = {'picks': [], 'declines': []}
            for team_key in alliance:
                if not re.match(r'frc\d+', str(team_key)):
                    raise ParserInputException("Bad team_key: '{}'. Must follow format: 'frcXXX'".format(team_key))
                else:
                    selection['picks'].append(team_key)
                    is_empty = False
            if not is_empty:
                alliance_selections.append(selection)
        return alliance_selections
