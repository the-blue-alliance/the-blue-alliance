import json
import logging

from datafeeds.datafeed_googledocs import DatafeedGoogleDocs
from datafeeds.googledocs_allianceselections_parser import GoogleDocsAllianceSelectionsParser
from models.event import Event


class DatafeedGoogleDocsAllianceSelection(DatafeedGoogleDocs):
    GDOCS_CSV_EXPORT_URL = 'https://docs.google.com/spreadsheet/ccc?key={0}&output=csv'

    YEAR_SPREADSHEET_KEY = {
        2014: '0ArVM96D1kMDzdE82Y2lCOW9yekJRc3EtUTZvZzZma3c'
    }

    def run(self, year):
        url = self.GDOCS_CSV_EXPORT_URL.format(self.YEAR_SPREADSHEET_KEY[year])
        data = self.parse(url, GoogleDocsAllianceSelectionsParser)
        events = []
        for event_short in data:
            event_id = str(year) + event_short.lower()
            event = Event.get_by_id(event_id)
            if not event:
                logging.warning('No event exists for: ' +event_id)
                continue
            event.alliance_selections_json = json.dumps(data[event_short])
            event.dirty = True  # FIXME Hack!
            events.append(event)
        return events
