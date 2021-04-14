import csv
import StringIO

from datafeeds.parser_base import ParserBase


class CSVTeamsParser(ParserBase):
    @classmethod
    def parse(self, data):
        """
        Parse CSV that contains teams
        Format is as follows:
        team1, team2, ... teamN
        Example:
        254, 1114, 100, 604, 148
        """
        teams = set()
        csv_data = list(csv.reader(StringIO.StringIO(data), delimiter=',', skipinitialspace=True))
        for row in csv_data:
            for team in row:
                if team.isdigit():
                    teams.add(int(team))
        return teams
