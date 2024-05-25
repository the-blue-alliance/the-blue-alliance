import csv
import StringIO

from datafeeds.parser_base import ParserBase


class CSVAllianceSelectionsParser(ParserBase):
    @classmethod
    def parse(self, data):
        """
        Parse CSV that contains teams
        Format is as follows:
        captain1, pick1-1, pick1-2
        captain2, pick2-1, pick2-2
        ...
        """
        alliances = []
        csv_data = list(csv.reader(StringIO.StringIO(data), delimiter=',', skipinitialspace=True))
        for row in csv_data:
            alliances.append({'picks': ['frc' + team.strip() for team in row], 'declines': []})
        return alliances
