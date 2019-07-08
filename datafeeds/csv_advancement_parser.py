import csv
import StringIO

from datafeeds.parser_base import ParserBase


class CSVAdvancementParser(ParserBase):
    @classmethod
    def parse(self, data, matches_per_team):
        """
        Parse CSV that contains round robin playoff advancement
        Format is as follows:
        alliance_number, cmp_points_m1, cmp_points_m2 ..., tiebreak1_m1, tiebreak2_m2 ...,  tiebreak2_m1, tiebreak2_m2 ..., wins, losses, ties
        """
        advancement = []
        csv_data = list(csv.reader(StringIO.StringIO(data), delimiter=',', skipinitialspace=True))
        for row in csv_data:
            advancement.append({
                'alliance_number': int(row[0]),
                'cmp_points_matches': [int(row[i]) for i in range(1, 1 + matches_per_team)],
                'tiebreak1_matches': [int(row[i]) for i in range(1 + matches_per_team, 1 + 2 * matches_per_team)],
                'tiebreak2_matches': [int(row[i]) for i in range(1 + 2 * matches_per_team, 1 + 3 * matches_per_team)],
                'wins': int(row[1 + 3 * matches_per_team]),
                'losses': int(row[2 + 3 * matches_per_team]),
                'ties': int(row[3 + 3 * matches_per_team]),
            })
        return advancement
