import datetime
import logging

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase

class FmsEventListParser(ParserBase):
    """
    Facilitates getting information about Events from USFIRST.
    Reads from FMS data pages, which are mostly tab delimited files wrapped in some HTML.
    """
    
    @classmethod
    def parse(self, html):
        """
        Parse the information table on USFIRSTs site to extract event information.
        Return a list of dictionaries of event data.
        """
        events = list()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        for title in soup.findAll('title'):
            if "FRC Team/Event List" not in title.string:
                return None
        
        event_rows = soup.findAll("pre")[0].string.split("\n")
        
        for line in event_rows[2:]: #first is blank, second is headers.
            data = line.split("\t")
            if len(data) > 1:
                try:
                    events.append({
                        "first_eid": data[0],
                        "name": data[1].strip(),
                        "venue": data[2],
                        "location": "%s, %s, %s" % (data[3], data[4], data[5]),
                        "start_date": self.splitDate(data[6]),
                        "end_date": self.splitDate(data[7]),
                        "year": int(data[8]),
                        "event_short": data[11].strip().lower()
                    })
                except Exception, e:
                    logging.warning("Failed to parse event row: %s" % data)
                    logging.warning(e)
        
        return events

    @classmethod
    def splitDate(self, date):
        try:
            (year, month, day) = date.split("-")
            date =  datetime.datetime(int(year), int(month), int(day))
            return date
        except Exception, e:
            return None
