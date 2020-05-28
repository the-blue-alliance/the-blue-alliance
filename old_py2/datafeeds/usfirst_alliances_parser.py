import json
import logging

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstAlliancesParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the table that contains alliances.
        """
        soup = BeautifulSoup(html)

        tables = soup.findAll('table')

        alliances = self.parseAlliances(tables[4])

        return alliances, False

    @classmethod
    def parseAlliances(self, table):
        alliances = []
        for tr in table.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) < 4:
                continue

            alliance_num_str = self._recurseUntilString(tds[0])
            if not alliance_num_str.isdigit():
                continue

            alliances.append({'picks': ['frc' + self._recurseUntilString(team_td) for team_td in tds[1:]], 'declines': []})

        return alliances if alliances != [] else None
