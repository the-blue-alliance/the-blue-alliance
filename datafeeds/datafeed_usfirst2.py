from datafeeds.datafeed_usfirst_base import DatafeedUsfirstBase

from datafeeds.fms_team_list_parser import FmsTeamListParser
from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
from datafeeds.usfirst_event_list_parser import UsfirstEventListParser
from datafeeds.usfirst_event_teams_parser import UsfirstEventTeamsParser
from datafeeds.usfirst_matches_parser import UsfirstMatchesParser

from models.event import Event
from models.match import Match
from models.team import Team

class DatafeedUsfirst2(DatafeedUsfirstBase):

    EVENT_DETAILS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_details&eid=%s&-session=myarea:%s"
    EVENT_LIST_REGIONALS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?event_type=FRC&season_FRC=%s"
    EVENT_TEAMS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_teamlist&results_size=250&eid=%s&-session=myarea:%s"
    EVENT_SHORT_EXCEPTIONS = {
        "arc": "Archimedes",
        "cur": "Curie",
        "gal": "Galileo",
        "new": "Newton",
    }

    MATCH_RESULTS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/matchresults.html" # % (year, event_short)
    MATCH_SCHEDULE_QUAL_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/schedulequal.html"
    MATCH_SCHEDULE_ELIMS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/scheduleelim.html"

    # Raw fast teamlist, no tpids
    FMS_TEAM_LIST_URL = "https://my.usfirst.org/frc/scoring/index.lasso?page=teamlist"

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
        url = self.EVENT_LIST_REGIONALS_URL_PATTERN % year
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

    def getMatches(self, event):
        url = self.MATCH_RESULTS_URL_PATTERN % (event.year,
            self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        matches = self.parse(url, UsfirstMatchesParser)

        return [Match(
            key_name = Match.getKeyName(
                event, 
                match.get("comp_level", None), 
                match.get("set_number", 0), 
                match.get("match_number", 0)),
            event = event.key(),
            game = Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number = match.get("set_number", 0),
            match_number = match.get("match_number", 0),
            comp_level = match.get("comp_level", None),
            team_key_names = match.get("team_key_names", None),
            alliances_json = match.get("alliances_json", None)
            )
            for match in matches]

    def getFmsTeamList(self):
        teams = self.parse(self.FMS_TEAM_LIST_URL, FmsTeamListParser)

        return [Team(
            key_name = "frc%s" % team.get("team_number", None),
            address = team.get("address", None),
            name = self._strForDb(team.get("name", None)),
            nickname = self._strForDb(team.get("nickname", None)),
            short_name = self._strForDb(team.get("short_name", None)),
            team_number = team.get("team_number", None)
            )
            for team in teams]

    def _strForDb(self, string):
        MAX_DB_LENGTH = 500
        if string:
            return string[:MAX_DB_LENGTH]
        else:
            return string
