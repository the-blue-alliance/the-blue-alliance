import csv
import logging
import StringIO
from datetime import datetime

from tba.consts.event_type import EventType
from datafeeds.parser_base import ParserBase


class OffseasonSpreadsheetParser(ParserBase):

    INDEX_TITLE = 1
    INDEX_VENUE = 3
    INDEX_LOCATION = 4
    INDEX_START = 6
    INDEX_END = 7
    INDEX_WEBSITE = 10

    @classmethod
    def parse(self, data):
        """
        Parse events from a csv spreadsheet
        """
        events = list()

        f = StringIO.StringIO(data)
        reader = csv.reader(f, delimiter=',')
        for row in reader:

            # Check required fields are there
            try:
                if not row[self.INDEX_TITLE] or not row[self.INDEX_START] or not row[self.INDEX_END]:
                    continue
            except IndexError:
                continue

            event = dict()

            event["name"] = row[self.INDEX_TITLE]
            event["venue"] = row[self.INDEX_VENUE]
            event["location"] = row[self.INDEX_LOCATION]
            try:
                event["start_date"] = datetime.strptime(row[self.INDEX_START], '%m/%d/%Y')
                event["end_date"] = datetime.strptime(row[self.INDEX_END], '%m/%d/%Y')
            except ValueError:
                # Invalid format date, skip this event
                logging.warning("Couln't parse dates {} or {}".format(row[self.INDEX_START], row[self.INDEX_END]))
                continue
            try:
                event["website"] = row[self.INDEX_WEBSITE]
            except IndexError:
                # No website, ignore
                pass
            event["event_type_enum"] = EventType.OFFSEASON
            events.append(event)

        return events, False
