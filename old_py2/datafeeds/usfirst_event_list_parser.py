from datetime import datetime
import urlparse
import logging

from bs4 import BeautifulSoup

from consts.district_type import DistrictType
from consts.event_type import EventType
from datafeeds.parser_base import ParserBase
from helpers.event_helper import EventHelper


class UsfirstEventListParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the list of events from USFIRST. This provides us with basic
        information about events and is how we first discover them.
        """
        events = list()
        soup = BeautifulSoup(html)

        for tr in soup.findAll('tr'):  # Events are in table rows
            event = dict()
            try:
                tds = tr.findAll('td')
                if tds[0].string is None:
                    # this may happen if this is a district event, in which case we can also extract the district name
                    event_type_str = unicode(tds[0].findAll(text=True)[2].string)

                    district_name_str = unicode(tds[0].findAll('em')[0].string)
                else:
                    event_type_str = unicode(tds[0].string)
                    district_name_str = None
                event["event_type_enum"] = EventHelper.parseEventType(event_type_str)
                event["event_district_enum"] = EventHelper.parseDistrictName(district_name_str)
                url_get_params = urlparse.parse_qs(urlparse.urlparse(tds[1].a["href"]).query)
                event["first_eid"] = url_get_params["eid"][0]

                event["name"] = ''.join(tds[1].a.findAll(text=True)).strip()  # <em>s in event names fix
                #event.venue = unicode(tds[2].string)
                #event.location = unicode(tds[3].string)

                # try:
                #    event_dates = str(tds[4].string).strip()
                #    event.start_date, event.stop_date = self.parseEventDates(event_dates)
                #    event.year = int(event_dates[-4:])
                # except Exception, detail:
                #    logging.error('Date Parse Failed: ' + str(detail))

                if event.get("event_type_enum", None) in EventType.NON_CMP_EVENT_TYPES:
                    events.append(event)

            except Exception, detail:
                logging.info('Event parsing failed: ' + str(detail))

        return events, False
