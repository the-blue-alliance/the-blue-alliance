import logging
import re

from google.appengine.api import memcache
from google.appengine.api import urlfetch

import tba_config

from helpers.team_helper import TeamTpidHelper

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
from datafeeds.usfirst_event_list_parser import UsfirstEventListParser
from datafeeds.usfirst_event_rankings_parser import UsfirstEventRankingsParser
from datafeeds.usfirst_event_awards_parser import UsfirstEventAwardsParser
from datafeeds.usfirst_event_teams_parser import UsfirstEventTeamsParser
from datafeeds.usfirst_matches_parser import UsfirstMatchesParser
from datafeeds.usfirst_team_details_parser import UsfirstTeamDetailsParser
from datafeeds.usfirst_team_events_parser import UsfirstTeamEventsParser

from models.event import Event
from models.award import Award
from models.match import Match
from models.team import Team


class DatafeedUsfirst(DatafeedBase):
    EVENT_LIST_REGIONALS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?event_type=FRC&season_FRC=%s"  # % (year)

    EVENT_DETAILS_URL_PATTERN = "http://www.usfirst.org/whats-going-on/event/%s"  # % (eid)
    EVENT_TEAMS_URL_PATTERN = "http://www.usfirst.org/whats-going-on/event/%s/teams?sort=asc&order=Team%%20Number"  # % (eid)
    TEAM_DETAILS_URL_PATTERN = "http://www.usfirst.org/whats-going-on/team/FRC/%s"  # % (tpid)

    EVENT_AWARDS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/awards.html"  # % (year, event_short)
    EVENT_RANKINGS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/rankings.html"  # % (year, event_short)
    MATCH_RESULTS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/matchresults.html"  # % (year, event_short)
    MATCH_SCHEDULE_QUAL_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/schedulequal.html"  # % (year, event_short)
    MATCH_SCHEDULE_ELIMS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/scheduleelim.html"  # % (year, event_short)
    EVENT_SHORT_EXCEPTIONS = {
        "arc": "Archimedes",
        "cur": "Curie",
        "gal": "Galileo",
        "new": "Newton",
    }

    def __init__(self, *args, **kw):
        self._session_key = dict()
        super(DatafeedUsfirst, self).__init__(*args, **kw)

    def getEventDetails(self, first_eid):
        url = self.EVENT_DETAILS_URL_PATTERN % (first_eid)
        event, _ = self.parse(url, UsfirstEventDetailsParser)

        return Event(
            id=str(event["year"]) + str.lower(str(event["event_short"])),
            end_date=event.get("end_date", None),
            event_short=event.get("event_short", None),
            event_type_enum=event.get("event_type_enum", None),
            first_eid=first_eid,
            name=event.get("name", None),
            official=True,
            start_date=event.get("start_date", None),
            venue_address=event.get("venue_address", None),
            venue=event.get("venue", None),
            location=event.get("location", None),
            website=event.get("website", None),
            year=event.get("year", None)
        )

    def getEventList(self, year):
        if type(year) is not int:
            raise TypeError("year must be an integer")
        url = self.EVENT_LIST_REGIONALS_URL_PATTERN % year
        events, _ = self.parse(url, UsfirstEventListParser)

        return [Event(
            event_type_enum=event.get("event_type_enum", None),
            event_short="???",
            first_eid=event.get("first_eid", None),
            name=event.get("name", None),
            year=int(year)
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
        awards, _ = self.parse(url, UsfirstEventAwardsParser)

        return [Award(
            id=Award.renderKeyName(event.key_name, award.get('name')),
            name=award.get('name', None),
            team=_getTeamKey(award),
            awardee=award.get('awardee', None),
            year=event.year,
            official_name=award.get('official_name', None),
            event=event.key)
            for award in awards]

    def getEventTeams(self, year, first_eid):
        """
        Returns a list of team_numbers attending a particular Event
        """
        if type(year) is not int:
            raise TypeError("year must be an integer")

        teams = []
        seen_teams = set()
        for page in range(8):  # Ensures this won't loop forever. 8 pages should be plenty.
            url = self.EVENT_TEAMS_URL_PATTERN % (first_eid)
            if page != 0:
                url += '&page=%s' % page
            partial_teams, more_pages = self.parse(url, UsfirstEventTeamsParser)
            teams.extend(partial_teams)

            partial_seen_teams = set([team['team_number'] for team in partial_teams])
            new_teams = partial_seen_teams.difference(seen_teams)
            if (not more_pages) or (new_teams == set()):
                break

            seen_teams = seen_teams.union(partial_seen_teams)

        return [Team(
            id="frc%s" % team.get("team_number", None),
            first_tpid=team.get("first_tpid", None),
            first_tpid_year=year,
            team_number=team.get("team_number", None)
            )
            for team in teams]

    def getMatches(self, event):
        url = self.MATCH_RESULTS_URL_PATTERN % (event.year,
                                                self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        matches, _ = self.parse(url, UsfirstMatchesParser)

        return [Match(
            id=Match.renderKeyName(
                event,
                match.get("comp_level", None),
                match.get("set_number", 0),
                match.get("match_number", 0)),
            event=event.key,
            game=Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number=match.get("set_number", 0),
            match_number=match.get("match_number", 0),
            comp_level=match.get("comp_level", None),
            team_key_names=match.get("team_key_names", None),
            time_string=match.get("time_string", None),
            alliances_json=match.get("alliances_json", None)
            )
            for match in matches]

    def getTeamDetails(self, team):
        if hasattr(team, 'first_tpid'):
            if team.first_tpid:
                url = self.TEAM_DETAILS_URL_PATTERN % (team.first_tpid)
                team_dict, _ = self.parse(url, UsfirstTeamDetailsParser)

                if "team_number" in team_dict:
                    return Team(
                        team_number=team_dict.get("team_number", None),
                        name=self._shorten(team_dict.get("name", None)),
                        address=team_dict.get("address", None),
                        nickname=team_dict.get("nickname", None),
                        website=team_dict.get("website", None)
                    )
                else:
                    logging.warning("No team_number found scraping %s, probably retired team" % team.team_number)
                    return None

        logging.warning('Null TPID for team %s' % team.team_number)
        return None

    def getTeamEvents(self, team):
        if hasattr(team, 'first_tpid'):
            if team.first_tpid:
                url = self.TEAM_DETAILS_URL_PATTERN % (team.first_tpid)
                first_eids, _ = self.parse(url, UsfirstTeamEventsParser)
                return first_eids

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
