import re
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from helpers.team_manipulator import TeamManipulator
from models.event import Event
from models.event_team import EventTeam
from models.favorite import Favorite
from models.team import Team


class TeamHelper(object):
    """
    Helper to sort teams and stuff
    """
    @classmethod
    def sortTeams(self, team_list):
        """
        Takes a list of Teams (not a Query object).
        """
        # Sometimes there are None objects in the list.
        team_list = filter(None, team_list)
        team_list = sorted(team_list, key=lambda team: team.team_number)

        return team_list

    @classmethod
    def getPopularTeamsEvents(self, events):
        events_by_key = {}
        for event in events:
            events_by_key[event.key.id()] = event

        # Calculate popular teams
        # Get cached team keys
        event_team_keys = memcache.get_multi(events_by_key.keys(), namespace='event-team-keys')

        # Get uncached team keys
        to_query = set(events_by_key.keys()).difference(event_team_keys.keys())
        event_teams_futures = [(
            event_key,
            EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async(projection=[EventTeam.team])
        ) for event_key in to_query]

        # Merge cached and uncached team keys
        for event_key, event_teams in event_teams_futures:
            event_team_keys[event_key] = [et.team.id() for et in event_teams.get_result()]
        memcache.set_multi(event_team_keys, 60*60*24, namespace='event-team-keys')

        team_keys = []
        team_events = {}
        for event_key, event_team_keys in event_team_keys.items():
            team_keys += event_team_keys
            for team_key in event_team_keys:
                team_events[team_key] = events_by_key[event_key]

        # Get cached counts
        team_favorite_counts = memcache.get_multi(team_keys, namespace='team-favorite-counts')

        # Get uncached counts
        to_count = set(team_keys).difference(team_favorite_counts.keys())
        count_futures = [(
            team_key,
            Favorite.query(Favorite.model_key == team_key).count_async()
        ) for team_key in to_count]

        # Merge cached and uncached counts
        for team_key, count_future in count_futures:
            team_favorite_counts[team_key] = count_future.get_result()
        memcache.set_multi(team_favorite_counts, 60*60*24, namespace='team-favorite-counts')

        # Sort to get top popular teams
        popular_team_keys = []
        for team_key, _ in sorted(team_favorite_counts.items(), key=lambda tc: -tc[1])[:25]:
            popular_team_keys.append(ndb.Key(Team, team_key))
        popular_teams =  sorted(ndb.get_multi(popular_team_keys), key=lambda team: team.team_number)

        popular_teams_events = []
        for team in popular_teams:
            popular_teams_events.append((team, team_events[team.key.id()]))

        return popular_teams_events


class TeamTpidHelper(object):

    # Separates tpids on the FIRST list of all teams.
    teamRe = re.compile(r'tpid=[A-Za-z0-9=&;\-:]*?"><b>\d+')
    # Extracts the team number from the team result.
    teamNumberRe = re.compile(r'\d+$')
    # Extracts the tpid from the team result.
    tpidRe = re.compile(r'\d+')
    # Extracts the link to the next page of results on the FIRST list of all teams.
    lastPageRe = re.compile(r'Next ->')

    TPID_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=searchresults&programs=FRC&reports=teams&sort_teams=number&results_size=250&omit_searchform=1&season_FRC=%s&skip_teams=%s"

    @classmethod
    def scrapeTpids(self, skip, year):
      """
      Searches the FIRST list of all teams for tpids, writing in the datastore.
      Also creates new Team objects.

      This code is modified from Pat Fairbank's frclinks source and modified
      to fit in the TBA framework. He has given us permission to borrow
      his code.
      """
      while 1:
        logging.info("Fetching 250 teams based on %s data, skipping %s" % (year, skip))

        tpids_dict = dict()

        # FIRST is now checking the 'Referer' header for the string 'usfirst.org'.
        # See https://github.com/patfair/frclinks/commit/051bf91d23ca0242dad5b1e471f78468173f597f
        teamList = urlfetch.fetch(self.TPID_URL_PATTERN % (year, skip), headers={'Referrer': 'usfirst.org'}, deadline=10)
        teamResults = self.teamRe.findall(teamList.content)

        for teamResult in teamResults:
          teamNumber = self.teamNumberRe.findall(teamResult)[0]
          teamTpid = self.tpidRe.findall(teamResult)[0]

          logging.info("Team %s TPID was %s in year %s." % (teamNumber, teamTpid, year))
          tpids_dict[teamNumber] = teamTpid

        teams = [Team(
              team_number=int(team_number),
              first_tpid=int(tpids_dict[team_number]),
              first_tpid_year=int(year),
              id="frc" + str(team_number)
            )
        for team_number in tpids_dict]

        TeamManipulator.createOrUpdate(teams)
        skip = int(skip) + 250

        # Handle degenerate cases.
        if skip > 10000:
          return None

        if len(self.lastPageRe.findall(teamList.content)) == 0:
          return None
