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
        result = dict()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        for tr in soup.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) > 1:
                field = str(tds[0].string)
                if field == "Event":
                    result["name"] = unicode(''.join(tds[1].findAll(text=True))).strip()
                if field == "Event Subtype":
                    result["event_type"] = EventHelper.parseEventType(unicode(tds[1].string))
                if field == "When":
                    try:
                        event_dates = str(tds[1].string).strip()
                        result["start_date"], result["end_date"] = self._parseEventDates(event_dates)
                        result["year"] = int(event_dates[-4:])
                    except Exception, detail:
                        logging.error('Date Parse Failed: ' + str(detail))
                if field == "Where":
                    # TODO: This next line is awful. Make this suck less.
                    # I think \t tabs mess it up or something. -greg 5/20/2010
                    result["venue_address"] = unicode(''.join(tds[1].findAll(text=True))).encode('ascii', 'ignore').strip().replace("\t","").replace("\r\n\r\n", "\r\n")
                if field == "Event Info":
                    result["website"] = unicode(tds[1].a['href'])
                if field == "Match Results":
                    #http://www2.usfirst.org/2010comp/Events/SDC/matchresults.html
                    m = re.match(r"http://www2\.usfirst\.org/%scomp/Events/([a-zA-Z0-9]*)/matchresults\.html" % result["year"], tds[1].a["href"])
                    if m is None:
                        # Some 2013 events are beautiful-souping tds[1].a["href"] to "http://www2.usfirst.org/2013comp/Events/FLBR" inexplicbly
                        m = re.match(r"http://www2\.usfirst\.org/%scomp/Events/([a-zA-Z0-9]*)" % result["year"], tds[1].a["href"])
                    result["event_short"] = m.group(1).lower()
        
        return result

    @classmethod
    def _parseEventDates(self, datestring):
        """
        Parses the date string provided by USFirst into actual event start and stop DateTimes.
        FIRST date strings look like "01-Apr - 03-Apr-2010".
        """
        month_dict = {"Jan":1,"Feb":2,"Mar":3,"Apr":4, "May":5, "Jun":6,
            "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        
        # "01-Apr - 03-Apr-2010"
        start_day = int(datestring[0:2])
        start_month = month_dict[datestring[3:6]]
        start_year = int(datestring[-4:])
        
        stop_day = int(datestring[9:11])
        stop_month = month_dict[datestring[12:15]]
        stop_year = int(datestring[-4:])
        
        start_date = datetime.datetime(start_year, start_month, start_day)
        stop_date = datetime.datetime(stop_year, stop_month, stop_day)
        
        return (start_date, stop_date)