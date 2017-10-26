from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstEventRankingsParser(ParserBase):
    """
    Works for official events from 2007-2012
    """
    @classmethod
    def parse(self, html):
        """
        Parse the rankings from USFIRST.
        """
        soup = BeautifulSoup(html)

        rankings = []
        tables = soup.findAll('table')
        rankings_table = tables[2]

        for tr in rankings_table.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) > 1:
                row = []
                for td in tds:
                    row.append(str(self._html_unescape(self._recurseUntilString(td))))
                rankings.append(row)

        return rankings, False
