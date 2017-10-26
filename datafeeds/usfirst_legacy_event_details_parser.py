import datetime
import logging
import re

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase
from helpers.event_helper import EventHelper


class UsfirstLegacyEventDetailsParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse an event's details page from USFIRST.
        """
        # locality_regions look like this:
        # <locality>, <region> <random string can have spaces>
        event_locality_region_re = r'(.*?), ([^ ]*)'

        result = dict()
        soup = BeautifulSoup(html)

        for tr in soup.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) > 1:
                field = str(tds[0].string)
                if field == "Event":
                    result["name"] = unicode(''.join(tds[1].findAll(text=True))).strip()
                    result['short_name'] = EventHelper.getShortName(result['name'])
                if field == "Event Subtype":
                    result["event_type_enum"] = EventHelper.parseEventType(unicode(tds[1].string))
                if field == "When":
                    try:
                        event_dates = str(tds[1].string).strip()
                        result["start_date"], result["end_date"] = self._parseEventDates(event_dates)
                        result["year"] = int(event_dates[-4:])
                    except Exception, detail:
                        logging.error('Date Parse Failed: ' + str(detail))
                if field == "Where":
                    address_lines_stripped = [re.sub('\s+', ' ', line.replace(u'\xa0', ' ')).strip() for line in tds[1].findAll(text=True)]
                    result["venue_address"] = unicode('\r\n'.join(address_lines_stripped)).encode('ascii', 'ignore')

                    match = re.match(event_locality_region_re, address_lines_stripped[-2])
                    locality, region = match.group(1), match.group(2)
                    country = address_lines_stripped[-1]
                    result['location'] = '%s, %s, %s' % (locality, region, country)
                if field == "Event Info":
                    result["website"] = unicode(tds[1].a['href'])
                if field == "Match Results":
                    #http://www2.usfirst.org/2010comp/Events/SDC/matchresults.html
                    m = re.match(r"http://www2\.usfirst\.org/%scomp/Events/([a-zA-Z0-9]*)/matchresults\.html" % result["year"], tds[1].a["href"])
                    if m is None:
                        # Some 2013 events are beautiful-souping tds[1].a["href"] to "http://www2.usfirst.org/2013comp/Events/FLBR" inexplicbly
                        m = re.match(r"http://www2\.usfirst\.org/%scomp/Events/([a-zA-Z0-9]*)" % result["year"], tds[1].a["href"])
                    result["event_short"] = m.group(1).lower()

        self._html_unescape_items(result)

        return result, False

    @classmethod
    def _parseEventDates(self, datestring):
        """
        Parses the date string provided by USFirst into actual event start and stop DateTimes.
        FIRST date strings look like "01-Apr - 03-Apr-2010" or "09-Mar-2005".
        """
        month_dict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                      "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

        # "01-Apr - 03-Apr-2010"
        # or "09-Mar-2005"
        if " - " in datestring:
            start_day = int(datestring[0:2])
            start_month = month_dict[datestring[3:6]]
            start_year = int(datestring[-4:])

            stop_day = int(datestring[9:11])
            stop_month = month_dict[datestring[12:15]]
            stop_year = int(datestring[-4:])

            start_date = datetime.datetime(start_year, start_month, start_day)
            stop_date = datetime.datetime(stop_year, stop_month, stop_day)
        else:
            day = int(datestring[0:2])
            month = month_dict[datestring[3:6]]
            year = int(datestring[-4:])

            start_date = datetime.datetime(year, month, day)
            stop_date = datetime.datetime(year, month, day)

        return (start_date, stop_date)
