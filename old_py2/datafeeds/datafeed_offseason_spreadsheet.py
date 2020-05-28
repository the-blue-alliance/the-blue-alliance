import datetime
import logging

from datafeeds.google_sheets_datafeed_base import GoogleSheetsDatafeedBase
from datafeeds.parsers.csv.offseason_spreadsheet_parser import OffseasonSpreadsheetParser

from models.event import Event


class DatafeedOffseasonSpreadsheet(GoogleSheetsDatafeedBase):
    # format with spreadsheet key
    SPREADSHEET_URL_BASE = "https://docs.google.com/spreadsheet/ccc?key={}&output=csv&hl"

    def getEventList(self, key):
        url = self.SPREADSHEET_URL_BASE.format(key)
        events, _ = self.parse(url, OffseasonSpreadsheetParser)

        return [Event(
            event_type_enum=event.get("event_type_enum", None),
            event_short="???",
            name=event.get("name", None),
            short_name=event.get("name", None),
            year=datetime.datetime.now().year,
            start_date=event.get("start_date", None),
            end_date=event.get("end_date", None),
            location=event.get("location", None),
            venue=event.get("venue", None),
            website=event.get("website", None),
        )for event in events]
