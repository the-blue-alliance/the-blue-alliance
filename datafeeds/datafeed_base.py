import logging

from google.appengine.api import urlfetch

class DatafeedBase(object):
    """
    Provides structure for fetching and parsing pages from websites.
    Other Datafeeds inherit from here.
    """
    def parse(self, url, parser):
        result = urlfetch.fetch(url, deadline=10)
        if result.status_code == 200:
            return parser.parse(result.content)
        else:
            logging.warning('Unable to retreive url: ' + (url))
            return list(), False

    def _shorten(self, string):
        MAX_DB_LENGTH = 500
        if string:
            return string[:MAX_DB_LENGTH]
        else:
            return string
