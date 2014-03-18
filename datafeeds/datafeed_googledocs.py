import cookielib
import json
import logging
import urllib2

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.googledocs_allianceselections_parser import GoogleDocsAllianceSelectionsParser
from models.event import Event


class DatafeedGoogleDocs(DatafeedBase):
    GDOCS_CSV_EXPORT_URL = 'https://docs.google.com/spreadsheet/ccc?key={0}&output=csv'

    YEAR_SPREADSHEET_KEY = {
        2014: '0ArVM96D1kMDzdE82Y2lCOW9yekJRc3EtUTZvZzZma3c'
    }

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

    def getAllianceSelections(self, year):
        url = self.GDOCS_CSV_EXPORT_URL.format(self.YEAR_SPREADSHEET_KEY[year])
        data = self.parse(url, GoogleDocsAllianceSelectionsParser)
        events = []
        for event_short in data:
            event_id = str(year) + event_short.lower()
            event = Event.get_by_id(event_id)
            if not event:
                logging.warning('No event exists for: ' + event_id)
                continue
            event.alliance_selections_json = json.dumps(data[event_short])
            event.dirty = True  # FIXME Hack!
            events.append(event)
        return events
