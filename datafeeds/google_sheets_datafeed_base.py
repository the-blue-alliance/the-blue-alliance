import logging

from datafeeds.datafeed_base import DatafeedBase
from helpers.url_opener import URLOpener


class GoogleSheetsDatafeedBase(DatafeedBase):
    """
    Class that uses a different url backend for requests
    Required because standard App Engine urlfetch doesn't
    keep cookies on redirect, which fetching data from
    Google Sheets requires
    """

    def parse(self, url, parser):
        opener = URLOpener()
        try:
            result = opener.open(url)
        except Exception, e:
            logging.error("URLFetch failed for: {}".format(url))
            logging.info(e)
            return [], False

        if result.status_code == 200:
            return parser.parse(result.content)
        else:
            logging.warning('Unable to retreive url: ' + (url))
            logging.warning("{}: {}".format(result.status_code, result.content))
            return [], False
