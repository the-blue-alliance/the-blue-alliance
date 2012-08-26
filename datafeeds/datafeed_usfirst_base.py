import logging
import re

from google.appengine.api import urlfetch

class DatafeedUsfirstBase(object):
    """
    Provides structure for fetching and parsing pages from FIRST's website.
    Other Datafeeds that parse FIRST inherit from here.
    """

    SESSION_KEY_GENERATING_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=searchresults&programs=FRC&reports=teams&omit_searchform=1&season_FRC=%s"

    def __init__(self):
        self._session_key = dict()

    def getSessionKey(self, year):
        """
        Grab a page from FIRST so we can get a session key out of URLs on it. This session
        key is needed to construct working event detail information URLs.
        """
        if self._session_key.get(year, False):
            return self._session_key.get(year)

        sessionRe = re.compile(r'myarea:([A-Za-z0-9]*)')
        
        result = urlfetch.fetch(self.SESSION_KEY_GENERATING_PATTERN % year, deadline=60)
        if result.status_code == 200:
            regex_results = re.search(sessionRe, result.content)
            if regex_results is not None:
                session_key = regex_results.group(1) #first parenthetical group
                if session_key is not None:
                    self._session_key[year] = session_key
                    return self._session_key[year]
            logging.error('Unable to get USFIRST session key for %s.' % year)
            return None
        else:
            logging.error('HTTP code %s. Unable to retreive url: %s' % 
                (result.status_code, self.SESSION_KEY_GENERATING_URL))

    def parse(self, url, parser):
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return parser.parse(result.content)
        else:
            logging.error('Unable to retreive url: ' + (url))
