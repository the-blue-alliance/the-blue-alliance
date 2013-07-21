import datetime
import logging
import re

from BeautifulSoup import BeautifulSoup

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
        
        result = dict()
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        page_title = soup.find('h1', {'id': 'thepagetitle'}).text
        result['name'] = unicode(re.sub(r'\([^)]*\)', '', page_title[4:]).strip())
        result['event_type_enum'] = EventHelper.parseEventType(unicode(re.search(event_type_re, page_title).group(1).strip()))
        
        try:
            event_dates = soup.find('div', {'class': 'event-dates'}).text
            result['start_date'], result['end_date'] = self._parseEventDates(event_dates)
            result['year'] = int(event_dates[-4:])
        except Exception, detail:
            logging.error('Date Parse Failed: ' + str(detail))
        
        # TODO: This next line is awful. Make this suck less.
        address = soup.find('div', {'class': 'event-address'})
        if address is not None:
            result['venue_address'] = unicode('\r\n'.join(line.strip() for line in address.findAll(text=True))).encode('ascii', 'ignore').strip().replace("\t","").replace("\r\n\r\n", "\r\n")
        
        website_tag = soup.find('div', {'class': 'event-info-link'})
        if website_tag is not None:
            result['website'] = unicode(website_tag.find('a')['href'])
        
        # http://www2.usfirst.org/2010comp/Events/SDC/matchresults.html
        match_results_url = soup.find('div', {'class': 'event-match-results'}).find('a')['href']
        m = re.match(r"http://www2\.usfirst\.org/%scomp/Events/([a-zA-Z0-9]*)/matchresults\.html" % result["year"], match_results_url)
        result['event_short'] = unicode(m.group(1).lower())
        
        return result, False

    @classmethod
    def _parseEventDates(self, datestring):
        """
        Parses the date string provided by USFirst into actual event start and stop DateTimes.
        FIRST date strings look like "01-Apr to 03-Apr-2010".
        """
        month_dict = {"Jan":1,"Feb":2,"Mar":3,"Apr":4, "May":5, "Jun":6,
            "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        
        # "01-Apr to 03-Apr-2010"
        start_day = int(datestring[0:2])
        start_month = month_dict[datestring[3:6]]
        start_year = int(datestring[-4:])
        
        stop_day = int(datestring[10:12])
        stop_month = month_dict[datestring[13:16]]
        stop_year = int(datestring[-4:])
        
        start_date = datetime.datetime(start_year, start_month, start_day)
        stop_date = datetime.datetime(stop_year, stop_month, stop_day)
        
        return (start_date, stop_date)
