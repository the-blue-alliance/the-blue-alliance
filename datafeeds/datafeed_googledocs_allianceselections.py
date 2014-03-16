import cookielib
import json
import urllib2

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.googledocs_allianceselections_parser import GoogleDocsAllianceSelectionsParser
from models.event import Event
# Nabbed some code from
# http://stackoverflow.com/questions/12842341/download-google-docs-public-spreadsheet-to-csv-with-python


class DatafeedGoogleDocsAllianceSelection(DatafeedBase):
    GDOCS_CSV_EXPORT_URL = 'https://docs.google.com/spreadsheet/ccc?key={0}&output=csv'

    YEAR_SPREADSHEET_KEY = {
        2014: '0ArVM96D1kMDzdE82Y2lCOW9yekJRc3EtUTZvZzZma3c'
    }

    def fetch_csv(self, year):
        url = self.GDOCS_CSV_EXPORT_URL.format(self.YEAR_SPREADSHEET_KEY[year])
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        resp = opener.open(url)
        data = resp.read()
        return data

    def run(self, year):
        data = GoogleDocsAllianceSelectionsParser.parse(self.fetch_csv(year))
        for eventcode in data:
            yrcode = str(year) + eventcode.lower()
            event = Event.get_by_id(yrcode)
            event.alliance_selections_json = json.dumps(data[eventcode])
            event.put()
