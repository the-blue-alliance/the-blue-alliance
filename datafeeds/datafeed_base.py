import logging

from google.appengine.api import urlfetch


class DatafeedBase(object):
    """
    Provides structure for fetching and parsing pages from websites.
    Other Datafeeds inherit from here.
    """

    def parse(self, url, parser, usfirst_session_key=None):
        headers = {
            'Cache-Control': 'no-cache, max-age=10',
            'Pragma': 'no-cache',
        }
        if 'my.usfirst.org/myarea' in url:
            # FIRST is now checking the 'Referer' header for the string 'usfirst.org'.
            # See https://github.com/patfair/frclinks/commit/051bf91d23ca0242dad5b1e471f78468173f597f
            headers['Referer'] = 'usfirst.org'
        if usfirst_session_key is not None:
            headers['Cookie'] = usfirst_session_key

        try:
            result = urlfetch.fetch(url, headers=headers, deadline=10)
        except Exception, e:
            logging.error("URLFetch failed for: {}".format(url))
            logging.info(e)
            return [], False

        if result.status_code == 200:
            return parser.parse(result.content)
        else:
            logging.warning('Unable to retreive url: ' + (url))
            return [], False

    def _shorten(self, string):
        MAX_DB_LENGTH = 500
        if string:
            return string[:MAX_DB_LENGTH]
        else:
            return string
