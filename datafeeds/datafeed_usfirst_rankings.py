import logging

from google.appengine.api import urlfetch
from datafeeds.datafeed_helper import recurseUntilString

from BeautifulSoup import BeautifulSoup

class DatafeedUsfirstRankings(object):
    """
    Works for official events from 2007-2012
    """
    
    EVENT_SHORT_EXCEPTIONS = {
        "arc": "Archimedes",
        "cur": "Curie",
        "gal": "Galileo",
        "new": "Newton",
    }
    
    RANKINGS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/rankings.html" # % (year, event_short)
    
    def getRankings(self, event):
        """
        Return a list of Rankings based on the FIRST match results page.
        The 0th element is the header.
        """
        
        url = self.RANKINGS_URL_PATTERN % (event.year,
            self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return self.parseRankings(event, result.content)
        else:
            logging.error('Unable to retreive url: ' + url)
    
    
    def parseRankings(self, event, html):
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
