import logging
import re
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import db

from BeautifulSoup import BeautifulSoup

from models import Event

class DatafeedUsfirstEvents(object):
    """
    Facilitates grabbing Regional Event information from USFIRST.org. It
    enables discovering and getting detailed information on official FIRST
    events. It returns Event model objects, but does no database IO itself.
    """
    
    # The types of events listed in the event list:
    REGIONAL_EVENT_TYPES = ["Regional", "MI FRC State Championship", "MI District"]
    
    # The URL for the event list:
    REGIONAL_EVENTS_URL = "https://my.usfirst.org/myarea/index.lasso?event_type=FRC&season_FRC=%s"
    # The URL pattern for specific event pages, based on their USFIRST event id.
    EVENT_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_details&eid=%s&-session=myarea:%s"
    # A URL that gives us session keyed URLs.
    SESSION_KEY_GENERATING_URL = "https://my.usfirst.org/myarea/index.lasso?page=searchresults&programs=FRC&reports=teams&omit_searchform=1&season_FRC=2011"
    
    def getSessionKey(self):
        """
        Grab a page from FIRST so we can get a session key out of URLs on it. This session
        key is needed to construct working event detail information URLs.
        """
        sessionRe = re.compile(r'myarea:([A-Za-z0-9]*)')
        
        result = urlfetch.fetch(self.SESSION_KEY_GENERATING_URL)
        if result.status_code == 200:
            regex_results = re.search(sessionRe, result.content)
            if regex_results is not None:
                session_key = regex_results.group(1) #first parenthetical group
                if session_key is not None:
                    return session_key
            logging.error('Unable to get USFIRST session key.')
            return None
        else:
            logging.error('Unable to retreive url: ' + self.SESSION_KEY_GENERATING_URL)
    
    def getEventList(self, year):
        """
        Return a list of Event objects from the FIRST event listing page.
        """
        result = urlfetch.fetch(self.REGIONAL_EVENTS_URL % year)
        if result.status_code == 200:
            return self.parseEventList(result.content)
        else:
            logging.error('Unable to retreive url: ' + (self.REGIONAL_EVENTS_URL % year))
    
    def getEvent(self, eid):
        """
        Return an Event object for a particular FIRST "event id" aka "eid"
        """
        session_key = self.getSessionKey()
        url = self.EVENT_URL_PATTERN % (eid, session_key)
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            event = self.parseEvent(result.content)
            event.first_eid = eid
            event.official = True
            return event
        else:
            logging.error('Unable to retreive url: ' + url)
    
    def parseEventList(self, html):
        """
        Parse the list of events from USFIRST. This provides us with basic
        information about events and is how we first discover them. Sends back
        a list of dictionaries.
        """
        events = list()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        for tr in soup.findAll('tr'): #Events are in table rows
            event = dict()
            #event = Event()
            try:
                tds = tr.findAll('td')
                #event.official = True
                event["event_type"] = unicode(tds[0].string)
                event["first_eid"] = tds[1].a["href"][24:28]
                event["name"] = ''.join(tds[1].a.findAll(text=True)) #<em>s in event names fix
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
                logging.error('Event parsing failed: ' + str(detail))  
            
        return events
    
    def parseEvent(self, html):
        """
        Parse an event's specific page HTML from USFIRST into the individual 
        fields of an Event object. This updates events and gets us fuller
        information once we know about this.
        """
        event_dict = dict()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        for tr in soup.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) > 1:
                field = str(tds[0].string)
                if field == "Event":
                    event_dict["name"] = unicode(''.join(tds[1].findAll(text=True)))
                if field == "Event Subtype":
                    event_dict["event_type"] = unicode(tds[1].string)
                if field == "When":
                    try:
                        event_dates = str(tds[1].string).strip()
                        event_dict["start_date"], event_dict["end_date"] = self.parseEventDates(event_dates)
                        event_dict["year"] = int(event_dates[-4:])
                    except Exception, detail:
                        logging.error('Date Parse Failed: ' + str(detail))
                if field == "Where":
                    # TODO: This next line is awful. Make this suck less.
                    # I think \t tabs mess it up or something. -greg 5/20/2010
                    event_dict["venue_address"] = unicode(''.join(tds[1].findAll(text=True))).encode('ascii', 'ignore')
                if field == "Event Info":
                    event_dict["website"] = unicode(tds[1].a['href'])
                if field == "Match Results":
                    #http://www2.usfirst.org/2010comp/Events/SDC/matchresults.html
                    m = re.match(r"http://www2\.usfirst\.org/%scomp/Events/([a-zA-Z0-9]*)/matchresults\.html" % event_dict["year"], tds[1].a["href"])
                    event_dict["event_short"] = m.group(1).lower()
        
        event = Event(
            key_name = str(event_dict["year"]) + str.lower(str(event_dict["event_short"])),
            name = event_dict.get("name", None),
            event_type = event_dict.get("event_type", None),
            start_date = event_dict.get("start_date", None),
            end_date = event_dict.get("end_date", None),
            year = event_dict.get("year", None),
            venue_address = event_dict.get("venue_address", None),
            website = event_dict.get("website", None),
            event_short = event_dict.get("event_short", None)
        )
                            
        return event
    
    def parseEventDates(self, datestring):
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
        
        start_date = datetime(start_year, start_month, start_day)
        stop_date = datetime(stop_year, stop_month, stop_day)
        
        return (start_date, stop_date)
