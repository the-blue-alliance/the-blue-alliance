import cookielib
import logging
import urllib2

from datafeeds.datafeed_base import DatafeedBase


class DatafeedGoogleDocs(DatafeedBase):
    """
    General Datafeed for anything that wants to fetch
    from Google Docs
    """
    def _fetch_url(self, url):
        """
        Google Docs uses a bunch of 302's when providing the data, and expects
        that the cookies are passed along with them
        See http://stackoverflow.com/questions/12842341/download-google-docs-public-spreadsheet-to-csv-with-python
        for some more info.
        """
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        try:
            resp = opener.open(url)
            data = resp.read()
            return data
        except urllib2.URLError, e:
            logging.warning('Unable to retrieve url: ' + url)
