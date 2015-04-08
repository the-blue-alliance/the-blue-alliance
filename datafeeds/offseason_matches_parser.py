import json
import logging
import csv
import StringIO
import re

from datafeeds.parser_base import ParserBase


class OffseasonMatchesParser(ParserBase):
    @classmethod
    def parse(self, data):
        """
        Parse CSV that contains match results.
        Format is as follows:
        match_id, red1, red2, red3, blue1, blue2, blue3, red score, blue score

        Example formats of match_id:
        qm1, sf2m1, f1m1
        """
        matches = list()

        csv_data = list(csv.reader(StringIO.StringIO(data), delimiter=',', skipinitialspace=True))
        for row in csv_data:
            matches.append(self.parseCSVMatch(row))

        return matches, False

    @classmethod
    def parseCSVMatch(self, row):
        match_id, red_1, red_2, red_3, blue_1, blue_2, blue_3, red_score, blue_score = row
        for i in range(len(row)):
            row[i] = row[i].strip()

        team_key_names = []

        red_teams = [red_1, red_2, red_3]
        red_team_strings = []
        for team in red_teams:
            red_team_strings.append('frc' + team.upper())
            if team.isdigit():
                team_key_names.append('frc' + team.upper())

        blue_teams = [blue_1, blue_2, blue_3]
        blue_team_strings = []
        for team in blue_teams:
            blue_team_strings.append('frc' + team.upper())
            if team.isdigit():
                team_key_names.append('frc' + team.upper())

        if not red_score:
            red_score = -1
        else:
            red_score = int(red_score)

        if not blue_score:
            blue_score = -1
        else:
            blue_score = int(blue_score)

        comp_level, match_number, set_number = self.parseMatchNumberInfo(match_id)

        alliances = {"red": {"teams": red_team_strings,
                             "score": red_score},
                     "blue": {"teams": blue_team_strings,
                              "score": blue_score}}

        match = {"alliances_json": json.dumps(alliances),
                 "comp_level": comp_level,
                 "match_number": match_number,
                 "set_number": set_number,
                 "team_key_names": team_key_names}

        return match

    @classmethod
    def parseMatchNumberInfo(self, string):
        string = string.strip()
        COMP_LEVEL_MAP = {'qm': 'qm',
                          'efm': 'ef',
                          'qfm': 'qf',
                          'sfm': 'sf',
                          'fm': 'f', }

        MATCH_PARSE_STYLE = {'qm': self.parseQualMatchNumberInfo,
                             'ef': self.parseElimMatchNumberInfo,
                             'qf': self.parseElimMatchNumberInfo,
                             'sf': self.parseElimMatchNumberInfo,
                             'f': self.parseElimMatchNumberInfo, }

        pattern = re.compile('[0-9]')
        comp_level = COMP_LEVEL_MAP[pattern.sub('', string)]

        match_number, set_number = MATCH_PARSE_STYLE[comp_level](string)
        return comp_level, match_number, set_number

    @classmethod
    def parseQualMatchNumberInfo(self, string):
        match_number = int(re.sub('\D', '', string))
        return match_number, 1

    @classmethod
    def parseElimMatchNumberInfo(self, string):
        set_number, match_number = string.split('m')
        match_number = int(match_number)
        set_number = int(set_number[-1])
        return match_number, set_number
