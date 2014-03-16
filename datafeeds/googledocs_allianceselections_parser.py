import csv
import StringIO


from datafeeds.parser_base import ParserBase
from helpers.event_helper import EventHelper


class GoogleDocsAllianceSelectionsParser(ParserBase):

    @classmethod
    def parse(cls, text):
        reader = csv.reader(StringIO.StringIO(text))
        # Someone unintelligently created this spreadsheet
        # around columns, and not rows. So...we'll remap it.
        data = {}  # Loaded with cls.populate_empty_events
        events = None  # Loaded as a list
        row_num = 0
        for row in reader:
            row_num += 1
            if row_num == 1:
                # Human readable-ish names
                continue
            if row_num == 2:
                # Event codes!
                # Note that the first member is blank
                events = row
                data = cls.populate_empty_events(events)
                continue
            if row_num < 27:
                col_num = 0
                for team in row:
                    col_num += 1
                    if col_num == 1:
                        continue
                    event_code = events[col_num-1]
                    alliance_num = cls.get_alliance_number(row_num)
                    data[event_code][alliance_num]['picks'].append('frc' + str(team))
        return data

    @classmethod
    def populate_empty_events(cls, events):
        d = {}
        for code in events[1:]:
            d[code] = {}
            # TODO we could probably use collections.defaultdict instead of this
            for i in range(1, 9):
                d[code][i] = {'picks': [], 'declines': []}
        return d

    @classmethod
    def get_alliance_number(cls, row_num):
        """
        Given the CSV row number, figure out what alliance
        the team is on
        """
        alliance = (row_num - 2) % 8
        if alliance == 0:
            alliance = 8
        return alliance