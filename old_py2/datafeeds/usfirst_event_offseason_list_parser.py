from datetime import datetime
import urlparse
import logging

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
        from bs4 import BeautifulSoup

        events = list()
        soup = BeautifulSoup(html)

        for table in soup.findAll('table'):
            trs = table.find('tbody').findAll('tr')
            for tr in trs:
                tds = tr.findAll('td')
                event = dict()
                for td in tds:
                    if td.get('class') and td["class"].count('views-field-title') > 0:
                        event["first_eid"] = td.a["href"].split("/")[-1]
                        event["name"] = " ".join(td.a.text.split(" ")[:-1])
                        event["state_prov"] = str(td.a.text.split(" ")[-1]).translate(None, "()")
                    for span in td.findAll('span'):
                        if span["class"].count("date-display-start") > 0:
                            event["start_date"] = datetime.strptime(span["content"][:10], "%Y-%m-%d")
                        if span["class"].count("date-display-end") > 0:
                            event["end_date"] = datetime.strptime(span["content"][:10], "%Y-%m-%d")
                        if span["class"].count("date-display-single") > 0:
                            event["start_date"] = datetime.strptime(span["content"][:10], "%Y-%m-%d")
                            event["end_date"] = datetime.strptime(span["content"][:10], "%Y-%m-%d")
                event["event_type_enum"] = EventType.OFFSEASON
                events.append(event)

        return events, False
