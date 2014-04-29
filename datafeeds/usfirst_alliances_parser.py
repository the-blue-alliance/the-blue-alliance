import json
import logging

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstAlliancesParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the table that contains alliances.
        """
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)

        tables = soup.findAll('table')

        alliances = self.parseAlliances(tables[4])

        return alliances, False

    @classmethod
    def parseAlliances(self, table):
        alliances = {}
        for tr in table.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) < 4:
                continue

            alliance_num_str = self._recurseUntilString(tds[0])
            if not alliance_num_str.isdigit():
                continue

            alliances[int(alliance_num_str)] = {'picks': [], 'declines': []}
            alliances[int(alliance_num_str)]['picks'] = ['frc' + self._recurseUntilString(team_td) for team_td in tds[1:]]

        return alliances if alliances != {} else None
