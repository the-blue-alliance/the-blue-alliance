import logging
import re

from google.appengine.api import urlfetch

from helpers.team_helper import TeamTpidHelper

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
from datafeeds.usfirst_event_list_parser import UsfirstEventListParser
from datafeeds.usfirst_event_rankings_parser import UsfirstEventRankingsParser
from datafeeds.usfirst_event_awards_parser import UsfirstEventAwardsParser
from datafeeds.usfirst_event_teams_parser import UsfirstEventTeamsParser
from datafeeds.usfirst_matches_parser import UsfirstMatchesParser
from datafeeds.usfirst_team_details_parser import UsfirstTeamDetailsParser

from models.event import Event
from models.award import Award
from models.match import Match
from models.team import Team

class DatafeedUsfirst(DatafeedBase):

    EVENT_AWARDS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/awards.html" # % (year, event_short)
    EVENT_DETAILS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_details&eid=%s&-session=myarea:%s"
    EVENT_LIST_REGIONALS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?event_type=FRC&season_FRC=%s"
    EVENT_RANKINGS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/rankings.html" # % (year, event_short)
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

    SESSION_KEY_GENERATING_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=searchresults&programs=FRC&reports=teams&omit_searchform=1&season_FRC=%s"

    TEAM_DETAILS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=team_details&tpid=%s&-session=myarea:%s"
    
    def __init__(self, *args, **kw):
        self._session_key = dict()
        super(DatafeedUsfirst, self).__init__(*args, **kw)

    def getSessionKey(self, year):
        """
        Grab a page from FIRST so we can get a session key out of URLs on it. This session
        key is needed to construct working event detail information URLs.
        """
        if self._session_key.get(year, False):
            return self._session_key.get(year)

        sessionRe = re.compile(r'myarea:([A-Za-z0-9]*)')
        
        result = urlfetch.fetch(self.SESSION_KEY_GENERATING_PATTERN % year, deadline=60)
        if result.status_code == 200:
            regex_results = re.search(sessionRe, result.content)
            if regex_results is not None:
                session_key = regex_results.group(1) #first parenthetical group
                if session_key is not None:
                    self._session_key[year] = session_key
                    return self._session_key[year]
            logging.error('Unable to get USFIRST session key for %s.' % year)
            return None
        else:
            logging.error('HTTP code %s. Unable to retreive url: %s' % 
                (result.status_code, self.SESSION_KEY_GENERATING_URL))

    def getEventDetails(self, year, first_eid):
        if type(year) is not int: raise TypeError("year must be an integer")
        url = self.EVENT_DETAILS_URL_PATTERN % (first_eid, self.getSessionKey(year))
        event = self.parse(url, UsfirstEventDetailsParser)

        return Event(
            id = str(event["year"]) + str.lower(str(event["event_short"])),
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

    def getEventRankings(self, event):
        url = self.EVENT_RANKINGS_URL_PATTERN % (event.year,
            self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        return self.parse(url, UsfirstEventRankingsParser)
    
    def getEventAwards(self, event):

        def _getTeamKey(award):
            team = Team.get_by_id('frc' + str(award.get('team_number', None)))
            if team is not None:
                return team.key
            else:
                return None

        url = self.EVENT_AWARDS_URL_PATTERN % (event.year,
            self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        awards = self.parse(url, UsfirstEventAwardsParser)
        
        return [Award(
            id = Award.renderKeyName(event.key_name, award.get('name')),
            name = award.get('name', None),
            team = _getTeamKey(award),
            awardee = award.get('awardee', None),
            year = event.year,
            official_name = award.get('official_name', None),
            event = event.key)
            for award in awards]

    def getEventTeams(self, year, first_eid):
        """
        Returns a list of team_numbers attending a particular Event
        """
        if type(year) is not int: raise TypeError("year must be an integer")
        url = self.EVENT_TEAMS_URL_PATTERN % (first_eid, self.getSessionKey(year))
        teams = self.parse(url, UsfirstEventTeamsParser)
        
        return [Team(
            id = "frc%s" % team.get("team_number", None),
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
            id = Match.renderKeyName(
                event, 
                match.get("comp_level", None), 
                match.get("set_number", 0), 
                match.get("match_number", 0)),
            event = event.key,
            game = Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number = match.get("set_number", 0),
            match_number = match.get("match_number", 0),
            comp_level = match.get("comp_level", None),
            team_key_names = match.get("team_key_names", None),
            time_string = match.get("time_string", None),
            alliances_json = match.get("alliances_json", None)
            )
            for match in matches]

    def getTeamDetails(self, team):
        if hasattr(team, 'first_tpid'):
            if team.first_tpid:
                session_key = self.getSessionKey(team.first_tpid_year)
                url = self.TEAM_DETAILS_URL_PATTERN % (team.first_tpid, session_key)
                team_dict = self.parse(url, UsfirstTeamDetailsParser)
                
                return Team(
                    team_number = team_dict.get("team_number", None),
                    name = self._shorten(team_dict.get("name", None)),
                    address = team_dict.get("address", None),
                    nickname = team_dict.get("nickname", None),
                    website = team_dict.get("website", None)
                )

        logging.warning('Null TPID for team %s' % team.team_number)
        return None

    def getTeamsTpids(self, year, skip=0):
        """
        Calling this function once establishes all of the Team objects in the Datastore.
        It does this by calling up USFIRST to search for Tpids. We have to do this in
        waves to avoid going over the GAE timeout.
        """
        # FIXME: This is not proper Datafeed form. -gregmarra 2012 Aug 26
        # TeamTpidHelper actually creates Team objects.
        TeamTpidHelper.scrapeTpids(skip, year)
