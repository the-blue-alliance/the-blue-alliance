from datafeeds.datafeed_helper import recurseUntilString

from BeautifulSoup import BeautifulSoup

from datafeeds.datafeed_parser_base import DatafeedParserBase

class UsfirstEventRankingsParser(DatafeedParserBase):
    """
    Works for official events from 2007-2012
    """
    @classmethod    
    def parse(self, html):
        """
        Parse the rankings from USFIRST.
        """
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        rankings = []
        tables = soup.findAll('table')
        rankings_table = tables[2]

        for tr in rankings_table.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) > 1:
                row = []
                for td in tds:
                    row.append(str(recurseUntilString(td)))
                rankings.append(row)
        return rankings
