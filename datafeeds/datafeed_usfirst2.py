from datafeeds.datafeed_usfirst_base import DatafeedUsfirstBase
from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
from datafeeds.usfirst_event_list_parser import UsfirstEventListParser
from datafeeds.usfirst_event_teams_parser import UsfirstEventTeamsParser

from models.event import Event
from models.team import Team

class DatafeedUsfirst2(DatafeedUsfirstBase):

    EVENT_DETAILS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_details&eid=%s&-session=myarea:%s"
    EVENT_LIST_REGIONALS_URL = "https://my.usfirst.org/myarea/index.lasso?event_type=FRC&season_FRC=%s"
    EVENT_TEAMS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_teamlist&results_size=250&eid=%s&-session=myarea:%s"

    def getEventDetails(self, year, first_eid):
        if type(year) is not int: raise TypeError("year must be an integer")
        url = self.EVENT_DETAILS_URL_PATTERN % (first_eid, self.getSessionKey(year))
        event = self.parse(url, UsfirstEventDetailsParser)

        return Event(
            key_name = str(event["year"]) + str.lower(str(event["event_short"])),
            end_date = event.get("end_date", None),
            event_short = event.get("event_short", None),
            event_type = event.get("event_type", None),
            first_eid = first_eid,
            name = event.get("name", None),
            official = True,
            start_date = event.get("start_date", None),
            venue_address = event.get("venue_address", None),
            website = event.get("website", None),
            year = event.get("year", None)
        )

    def getEventList(self, year):
        if type(year) is not int: raise TypeError("year must be an integer")
        url = self.EVENT_LIST_REGIONALS_URL % year
        events = self.parse(url, UsfirstEventListParser)

        return [Event(
            event_type = event.get("event_type", None),
            event_short = "???",
            first_eid = event.get("first_eid", None),
            name = event.get("name", None),
            year = int(year)
            )
            for event in events]

    def getEventTeams(self, year, first_eid):
        """
        Returns a list of team_numbers attending a particular Event
        """
        if type(year) is not int: raise TypeError("year must be an integer")
        url = self.EVENT_TEAMS_URL_PATTERN % (first_eid, self.getSessionKey(year))
        teams = self.parse(url, UsfirstEventTeamsParser)
        
        return [Team(
            key_name = "frc%s" % team.get("team_number", None),
            first_tpid = team.get("first_tpid", None),
            first_tpid_year = year,
            team_number = team.get("team_number", None)
            )
            for team in teams]
