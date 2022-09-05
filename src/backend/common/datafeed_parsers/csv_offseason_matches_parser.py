import csv
import json
import re
from io import StringIO


class CSVOffseasonMatchesParser:
    @classmethod
    def parse(cls, data):
        """
        Parse CSV that contains match results.
        Format is as follows:
        match_id, red1, red2, red3, blue1, blue2, blue3, red score, blue score

        Example formats of match_id:
        qm1, sf2m1, f1m1
        """
        matches = list()

        csv_data = list(
            csv.reader(StringIO(data), delimiter=",", skipinitialspace=True)
        )
        for row in csv_data:
            matches.append(cls.parse_csv_match(row))

        return matches, False

    @classmethod
    def parse_csv_match(cls, row):
        (
            match_id,
            red_1,
            red_2,
            red_3,
            blue_1,
            blue_2,
            blue_3,
            red_score,
            blue_score,
        ) = row
        for i in range(len(row)):
            row[i] = row[i].strip()

        team_key_names = []

        red_teams = [red_1, red_2, red_3]
        red_team_strings = []
        for team in red_teams:
            red_team_strings.append("frc" + team.upper())
            if team.isdigit():
                team_key_names.append("frc" + team.upper())

        blue_teams = [blue_1, blue_2, blue_3]
        blue_team_strings = []
        for team in blue_teams:
            blue_team_strings.append("frc" + team.upper())
            if team.isdigit():
                team_key_names.append("frc" + team.upper())

        if not red_score:
            red_score = -1
        else:
            red_score = int(red_score)

        if not blue_score:
            blue_score = -1
        else:
            blue_score = int(blue_score)

        comp_level, match_number, set_number = cls.parse_match_number_info(match_id)

        alliances = {
            "red": {"teams": red_team_strings, "score": red_score},
            "blue": {"teams": blue_team_strings, "score": blue_score},
        }

        match = {
            "alliances_json": json.dumps(alliances),
            "comp_level": comp_level,
            "match_number": match_number,
            "set_number": set_number,
            "team_key_names": team_key_names,
        }

        return match

    @classmethod
    def parse_match_number_info(cls, string):
        string = string.strip()
        COMP_LEVEL_MAP = {
            "qm": "qm",
            "efm": "ef",
            "qfm": "qf",
            "sfm": "sf",
            "fm": "f",
        }

        MATCH_PARSE_STYLE = {
            "qm": cls.parse_qual_match_number_info,
            "ef": cls.parse_elim_match_number_info,
            "qf": cls.parse_elim_match_number_info,
            "sf": cls.parse_elim_match_number_info,
            "f": cls.parse_elim_match_number_info,
        }

        pattern = re.compile("[0-9]")
        comp_level = COMP_LEVEL_MAP[pattern.sub("", string)]

        match_number, set_number = MATCH_PARSE_STYLE[comp_level](string)
        return comp_level, match_number, set_number

    @classmethod
    def parse_qual_match_number_info(cls, string):
        match_number = int(re.sub(r"\D", "", string))
        return match_number, 1

    @classmethod
    def parse_elim_match_number_info(cls, string):
        set_number, match_number = string.split("m")
        match_number = int(match_number)
        set_number = int(set_number[-1])
        return match_number, set_number
