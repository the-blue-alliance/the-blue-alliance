import datetime
import logging
import re

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase
from helpers.event_helper import EventHelper


class UsfirstEventDetailsParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse an event's details page from USFIRST.
        """
        # page_titles look like this:
        # <YEAR> <EVENT_NAME> (<EVENT_TYPE>)
        event_type_re = r'\((.+)\)'

        # locality_regions look like this:
        # <locality>, <region> <random string can have spaces>
        event_locality_region_re = r'(.*?), ([^ ]*)'

        result = dict()
        soup = BeautifulSoup(html)

        page_title = soup.find('h1', {'id': 'thepagetitle'}).text
        result['name'] = unicode(re.sub(r'\([^)]*\)', '', page_title[4:]).strip())
        result['short_name'] = EventHelper.getShortName(result['name'])
        result['event_type_enum'] = EventHelper.parseEventType(unicode(re.search(event_type_re, page_title).group(1).strip()))

        try:
            event_dates = soup.find('div', {'class': 'event-dates'}).text
            result['start_date'], result['end_date'] = self._parseEventDates(event_dates)
            result['year'] = int(event_dates[-4:])
        except Exception, detail:
            logging.error('Date Parse Failed: ' + str(detail))

        address = soup.find('div', {'class': 'event-address'})
        if address is not None:
            address_lines_stripped = [re.sub('\s+', ' ', line.replace(u'\xa0', ' ')).strip() for line in address.findAll(text=True)]
            result['venue_address'] = unicode('\r\n'.join(address_lines_stripped)).encode('ascii', 'ignore')

            if len(address_lines_stripped) >= 2:
                match = re.match(event_locality_region_re, address_lines_stripped[-2])
                locality, region = match.group(1), match.group(2)
                country = address_lines_stripped[-1]
                result['location'] = '%s, %s, %s' % (locality, region, country)
            if len(address_lines_stripped) >= 3:
                result['venue'] = address_lines_stripped[0]

        website_tag = soup.find('div', {'class': 'event-info-link'})
        if website_tag is not None:
            result['website'] = unicode(website_tag.find('a')['href'])

        # http://www2.usfirst.org/2010comp/Events/SDC/matchresults.html
        try:
            match_results_url = soup.find('div', {'class': 'event-match-results'}).find('a')['href']
            m = re.match(r"http://www2\.usfirst\.org/%scomp/Events/([a-zA-Z0-9]*)/" % result["year"], match_results_url)
            result['event_short'] = unicode(m.group(1).lower())
        except AttributeError, detail:
            logging.warning("Event short parse failed: {}".format(detail))
            return None, False

        self._html_unescape_items(result)

        return result, False

    @classmethod
    def _parseEventDates(self, datestring):
        """
        Parses the date string provided by USFirst into actual event start and stop DateTimes.
        FIRST date strings look like "01-Apr to 03-Apr-2010" or "09-Mar-2005".
        """
        month_dict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                      "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

        # "01-Apr to 03-Apr-2010"
        # or "09-Mar-2005"
        if "to" in datestring:
            start_day = int(datestring[0:2])
            start_month = month_dict[datestring[3:6]]
            start_year = int(datestring[-4:])

            stop_day = int(datestring[10:12])
            stop_month = month_dict[datestring[13:16]]
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
