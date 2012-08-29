from datetime import datetime
import logging

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase

class UsfirstEventListParser(ParserBase):

    REGIONAL_EVENT_TYPES = [
        "Regional",
        "MI FRC State Championship",
        "MI District",
        "Qualifying Event",
        "Qualifying Championship",
        "District Event",
        "District Championship"]

    @classmethod
    def parse(self, html):
        """
        Parse the list of events from USFIRST. This provides us with basic
        information about events and is how we first discover them.
        """
        events = list()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        for tr in soup.findAll('tr'): #Events are in table rows
            event = dict()
            try:
                tds = tr.findAll('td')
                event["event_type"] = unicode(tds[0].string)
                event["first_eid"] = tds[1].a["href"][24:28]
                event["name"] = ''.join(tds[1].a.findAll(text=True)).strip() #<em>s in event names fix
                #event.venue = unicode(tds[2].string)
                #event.location = unicode(tds[3].string)
                
                #try:
                #    event_dates = str(tds[4].string).strip()
                #    event.start_date, event.stop_date = self.parseEventDates(event_dates)
                #    event.year = int(event_dates[-4:])
                #except Exception, detail:
                #    logging.error('Date Parse Failed: ' + str(detail))

                if event.get("event_type", None) in self.REGIONAL_EVENT_TYPES:
                    events.append(event)

            except Exception, detail:
                logging.info('Event parsing failed: ' + str(detail))
            
        return events
