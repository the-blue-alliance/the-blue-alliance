import logging

from google.appengine.api import urlfetch

class DatafeedBase(object):
    """
    Provides structure for fetching and parsing pages from websites.
    Other Datafeeds inherit from here.
    """

    def parse(self, url, parser):
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return parser.parse(result.content)
        else:
            logging.error('Unable to retreive url: ' + (url))
