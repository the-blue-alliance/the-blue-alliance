import dateutil.parser
import urlparse
import logging

from BeautifulSoup import BeautifulSoup

from consts.event_type import EventType
from datafeeds.parser_base import ParserBase
from helpers.event_helper import EventHelper


class UsfirstEventOffseasonListParser(ParserBase):

    @classmethod
    def parse(self, html):
        """
        Parse the list of events from USFIRST. This provides us with basic
        information about events and is how we first discover them.
        """
        events = list()
        soup = BeautifulSoup(html,
                             convertEntities=BeautifulSoup.HTML_ENTITIES)

        for table in soup.findAll('table'):
            if table.find('caption').text.count('Off Season Events') > 0:
                trs = table.find('tbody').findAll('tr')
                for tr in trs:
                    tds = tr.findAll('td')
                    event = dict()
                    for td in tds:
                        if td["class"].count('views-field-title') > 0:
                            event["url_slug"] = td.a["href"].split("/")[-1]
                            event["name"] = " ".join(td.a.text.split(" ")[:-1])
                        for span in td.findAll('span'):
                            if span["class"].count("date-display-start") > 0:
                                event["start_date"] = dateutil.parser.parse(span["content"])
                            if span["class"].count("date-display-end") > 0:
                                event["end_date"] = dateutil.parser.parse(span["content"])
                    event["event_type_enum"] = EventType.OFFSEASON
                    events.append(event)

        return events, False
