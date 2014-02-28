import logging
import re

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

import tba_config

from consts.event_type import EventType

from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.team_helper import TeamTpidHelper

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
from datafeeds.usfirst_event_list_parser import UsfirstEventListParser
from datafeeds.usfirst_event_rankings_parser import UsfirstEventRankingsParser
from datafeeds.usfirst_event_awards_parser import UsfirstEventAwardsParser
from datafeeds.usfirst_event_awards_parser_02 import UsfirstEventAwardsParser_02
from datafeeds.usfirst_event_awards_parser_03_04 import UsfirstEventAwardsParser_03_04
from datafeeds.usfirst_event_awards_parser_05_06 import UsfirstEventAwardsParser_05_06
from datafeeds.usfirst_event_teams_parser import UsfirstEventTeamsParser
from datafeeds.usfirst_matches_parser import UsfirstMatchesParser
from datafeeds.usfirst_matches_parser_2002 import UsfirstMatchesParser2002
from datafeeds.usfirst_matches_parser_2003 import UsfirstMatchesParser2003
from datafeeds.usfirst_match_schedule_parser import UsfirstMatchScheduleParser
from datafeeds.usfirst_team_details_parser import UsfirstTeamDetailsParser
from datafeeds.usfirst_pre2003_team_events_parser import UsfirstPre2003TeamEventsParser

from models.event import Event
from models.award import Award
from models.match import Match
from models.team import Team


class DatafeedUsfirst(DatafeedBase):
    EVENT_LIST_REGIONALS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?event_type=FRC&season_FRC=%s"  # % (year)

    EVENT_DETAILS_URL_PATTERN = "http://www.usfirst.org/whats-going-on/event/%s?ProgramCode=FRC"  # % (eid)
    EVENT_TEAMS_URL_PATTERN = "http://www.usfirst.org/whats-going-on/event/%s/teams?sort=asc&order=Team%%20Number&ProgramCode=FRC"  # % (eid)
    TEAM_DETAILS_URL_PATTERN = "http://www.usfirst.org/whats-going-on/team/%s?ProgramCode=FRC"  # % (tpid)

    EVENT_AWARDS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/awards.html"  # % (year, event_short)
    EVENT_RANKINGS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/rankings.html"  # % (year, event_short)

    YEAR_MATCH_RESULTS_URL_PATTERN = {
        2003: "http://www2.usfirst.org/%scomp/events/%s/matchsum.html",  # % (year, event_short)
    }
    DEFAULT_MATCH_RESULTS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/matchresults.html"  # % (year, event_short)

    MATCH_SCHEDULE_QUAL_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/schedulequal.html"  # % (year, event_short)
    MATCH_SCHEDULE_ELIMS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/scheduleelim.html"  # % (year, event_short)
    EVENT_SHORT_EXCEPTIONS = {
        "arc": "Archimedes",
        "cur": "Curie",
        "gal": "Galileo",
        "new": "Newton",
        "ein": "Einstein",  # Only used for 2008ein due to FIRST's inconsistent naming
    }

    YEAR_MATCH_PARSER = {
        2002: UsfirstMatchesParser2002,
        2003: UsfirstMatchesParser2003,
    }
    DEFAULT_MATCH_PARSER = UsfirstMatchesParser

    MATCH_SCHEDULE_PARSER = UsfirstMatchScheduleParser

    YEAR_AWARD_PARSER = {
        2002: UsfirstEventAwardsParser_02,
        2003: UsfirstEventAwardsParser_03_04,
        2004: UsfirstEventAwardsParser_03_04,
        2005: UsfirstEventAwardsParser_05_06,
        2006: UsfirstEventAwardsParser_05_06,
    }
    DEFAULT_AWARD_PARSER = UsfirstEventAwardsParser

    def __init__(self, *args, **kw):
        self._session_key = dict()
        super(DatafeedUsfirst, self).__init__(*args, **kw)

    def getEventDetails(self, first_eid):
        url = self.EVENT_DETAILS_URL_PATTERN % (first_eid)
        event, _ = self.parse(url, UsfirstEventDetailsParser)
        if event is None:
            return None

        return Event(
            id=str(event["year"]) + str.lower(str(event["event_short"])),
            end_date=event.get("end_date", None),
            event_short=event.get("event_short", None),
            event_type_enum=event.get("event_type_enum", None),
            first_eid=first_eid,
            name=event.get("name", None),
            short_name=event.get("short_name", None),
            official=True,
            start_date=event.get("start_date", None),
            venue_address=event.get("venue_address", None),
            venue=event.get("venue", None),
            location=event.get("location", None),
            timezone_id=EventHelper.get_timezone_id(event),
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
        rankings, _ = self.parse(url, UsfirstEventRankingsParser)
        return rankings

    def getEventAwards(self, event):
        """
        Works reliably for regional events from 2002-present and
        championship events from 2007-present
        """
        if event.year < 2002 or (event.event_type_enum in EventType.CMP_EVENT_TYPES and event.year < 2007):
            # award pages malformatted
            logging.warning("Skipping awards parsing for event: {}".format(event.key_name))
            return []

        url = self.EVENT_AWARDS_URL_PATTERN % (event.year,
                                               self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        awards, _ = self.parse(url, self.YEAR_AWARD_PARSER.get(event.year, self.DEFAULT_AWARD_PARSER))

        return [Award(
            id=Award.render_key_name(event.key_name, award['award_type_enum']),
            name_str=award['name_str'],
            award_type_enum=award['award_type_enum'],
            year=event.year,
            event=event.key,
            event_type_enum=event.event_type_enum,
            team_list=[ndb.Key(Team, 'frc{}'.format(team_number)) for team_number in award['team_number_list']],
            recipient_json_list=award['recipient_json_list']
            )
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
        matches_url = self.YEAR_MATCH_RESULTS_URL_PATTERN.get(
            event.year, self.DEFAULT_MATCH_RESULTS_URL_PATTERN) % (
                event.year, self.EVENT_SHORT_EXCEPTIONS.get(event.event_short,
                                                            event.event_short))

        match_dicts, _ = self.parse(matches_url, self.YEAR_MATCH_PARSER.get(event.year, self.DEFAULT_MATCH_PARSER))
        if not match_dicts:  # Matches have been played, but qual match schedule may be out
            # If this is run when there are already matches in the DB, it will overwrite scores!
            # Check to make sure event has no existing matches
            if len(Match.query(Match.event == event.key).fetch(1, keys_only=True)) == 0:
                logging.warning("No matches found for {}. Trying to parse qual match schedule.".format(event.key.id()))

                match_sched_url = self.MATCH_SCHEDULE_QUAL_URL_PATTERN % (
                    event.year, self.EVENT_SHORT_EXCEPTIONS.get(event.event_short,
                                                                event.event_short))
                match_dicts, _ = self.parse(match_sched_url, self.MATCH_SCHEDULE_PARSER)

        matches = [Match(
            id=Match.renderKeyName(
                event.key.id(),
                match_dict.get("comp_level", None),
                match_dict.get("set_number", 0),
                match_dict.get("match_number", 0)),
            event=event.key,
            game=Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number=match_dict.get("set_number", 0),
            match_number=match_dict.get("match_number", 0),
            comp_level=match_dict.get("comp_level", None),
            team_key_names=match_dict.get("team_key_names", None),
            time_string=match_dict.get("time_string", None),
            alliances_json=match_dict.get("alliances_json", None)
            )
            for match_dict in match_dicts]

        MatchHelper.add_match_times(event, matches)
        return matches

    def getTeamDetails(self, team):
        if hasattr(team, 'first_tpid'):
            if team.first_tpid:
                url = self.TEAM_DETAILS_URL_PATTERN % (team.first_tpid)
                team_dict, _ = self.parse(url, UsfirstTeamDetailsParser)

                if team_dict is not None and "team_number" in team_dict:
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

    def getPre2003TeamEvents(self, team):
        if hasattr(team, 'first_tpid'):
            if team.first_tpid:
                url = self.TEAM_DETAILS_URL_PATTERN % (team.first_tpid)
                first_eids, _ = self.parse(url, UsfirstPre2003TeamEventsParser)
                return first_eids

        logging.warning('Null TPID for team %s' % team.team_number)
        return []

    def getTeamsTpids(self, year, skip=0):
        """
        Calling this function once establishes all of the Team objects in the Datastore.
        It does this by calling up USFIRST to search for Tpids. We have to do this in
        waves to avoid going over the GAE timeout.
        """
        # FIXME: This is not proper Datafeed form. -gregmarra 2012 Aug 26
        # TeamTpidHelper actually creates Team objects.
        TeamTpidHelper.scrapeTpids(skip, year)
