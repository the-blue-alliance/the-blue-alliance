import logging

from google.appengine.api import urlfetch


class DatafeedBase(object):
    """
    Provides structure for fetching and parsing pages from websites.
    Other Datafeeds inherit from here.
    """
    def fetch_url(self, url):
        result = urlfetch.fetch(url,
                                headers={'Cache-Control': 'no-cache, max-age=10',
                                         'Pragma': 'no-cache',
                                         },
                                deadline=10)
        if result.status_code == 200:
            return result.content
        else:
            logging.warning('Unable to retreive url: ' + url)
            return list(), False

    def parse(self, url, parser):
        content = self.fetch_url(url)
        return parser.parse(content)

    def _shorten(self, string):
        MAX_DB_LENGTH = 500
        if string:
            return string[:MAX_DB_LENGTH]
        else:
            return string
