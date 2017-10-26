import datetime
import logging

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class FmsEventListParser(ParserBase):
    """
    Facilitates getting information about Events from USFIRST.
    Reads from FMS data pages, which are mostly tab delimited files wrapped in some HTML.
    """

    @classmethod
    def parse(self, html):
        return self.parse_2014(html)

    @classmethod
    def parse_2012(self, html):
        """
        Parse the information table on USFIRSTs site to extract event information.
        Return a list of dictionaries of event data.
        Works for data from 2012.
        """
        events = list()
        soup = BeautifulSoup(html)

        for title in soup.findAll('title'):
            if "FRC Team/Event List" not in title.string:
                return None

        event_rows = soup.findAll("pre")[0].string.split("\n")

        for line in event_rows[2:]:  # first is blank, second is headers.
            data = line.split("\t")
            if len(data) > 1:
                try:
                    events.append({
                        "first_eid": data[0],
                        "name": data[1].strip(),
                        "venue": data[2],
                        "start_date": self.splitDate(data[6]),
                        "end_date": self.splitDate(data[7]),
                        "year": int(data[8]),
                        "event_short": data[11].strip().lower()
                    })
                except Exception, e:
                    logging.warning("Failed to parse event row: %s" % data)
                    logging.warning(e)

        return events, False

    @classmethod
    def parse_2014(self, html):
        """
        Parse the information table on USFIRSTs site to extract event information.
        Return a list of dictionaries of event data.
        Works for data from 2014.
        """
        events = list()
        soup = BeautifulSoup(html)

        for title in soup.findAll('title'):
            if "FRC Team/Event List" not in title.string:
                return None

        event_rows = soup.findAll("pre")[0].string.split("\n")

        for line in event_rows[2:]:  # first is blank, second is headers.
            data = line.split("\t")
            if len(data) > 1:
                try:
                    events.append({
                        "first_eid": data[0],
                        #"event_subtype": data[1],
                        #"id_event_subtype": data[2],
                        #"district_code": data[3],
                        #"id_district": data[4],
                        "name": data[5].strip(),
                        "venue": data[6],
                        #"city": data[7],
                        #"state": data[8],
                        #"country"": data[9],
                        "start_date": self.splitDate(data[10]),
                        "end_date": self.splitDate(data[11]),
                        "year": int(data[12]),
                        #"num_teams": int(data[13]),
                        #"url_team_list": data[14],
                        "event_short": data[15].strip().lower(),
                        "location": "{}, {}, {}".format(data[7], data[8], data[9])
                    })
                except Exception, e:
                    logging.info("Failed to parse event row: %s" % data)
                    logging.info(e)

        return events, False

    @classmethod
    def splitDate(self, date):
        try:
            (year, month, day) = date.split("-")
            date = datetime.datetime(int(year), int(month), int(day))
            return date
        except Exception, e:
            return None
