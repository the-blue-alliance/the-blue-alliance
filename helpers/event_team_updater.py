import datetime

from google.appengine.ext import ndb

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team


class EventTeamUpdater(object):
    @classmethod
    def update(self, event_key):
        """
        Updates EventTeams for an event.
        Returns a tuple of (teams, event_teams, event_team_keys_to_delete)
        An EventTeam is valid iff the team:
        a) played a match at the event,
        b) the team received an award at the event,
        c) the event has not yet occurred,
        d) the team is on an alliance
        e) or the event is not from the current year. (This is to make sure we don't delete old data we may no longer be able to scrape)
        """
        event = Event.get_by_id(event_key)
        cur_year = datetime.datetime.now().year

        # Add teams from Matches and Awards
        team_ids = set()
        match_key_futures = Match.query(
            Match.event == event.key).fetch_async(1000, keys_only=True)
        award_key_futures = Award.query(
            Award.event == event.key).fetch_async(1000, keys_only=True)
        match_futures = ndb.get_multi_async(match_key_futures.get_result())
        award_futures = ndb.get_multi_async(award_key_futures.get_result())

        for match_future in match_futures:
            match = match_future.get_result()
            for team in match.team_key_names:
                team_ids.add(team)
        for award_future in award_futures:
            award = award_future.get_result()
            for team_key in award.team_list:
                team_ids.add(team_key.id())

        # Add teams from Alliances
        for team in event.alliance_teams:
            team_ids.add(team)

        # Create or update EventTeams
        teams = [Team(id=team_id,
                      team_number=int(team_id[3:]))
                      for team_id in team_ids if team_id[3:].isdigit()]

        if teams:
            event_teams = [EventTeam(id=event_key + "_" + team.key.id(),
                                     event=event.key,
                                     team=team.key,
                                     year=event.year)
                                     for team in teams]
        else:
            event_teams = None

        # Delete EventTeams for teams who did not participate in the event
        # Only runs if event is over
        existing_event_teams_keys = EventTeam.query(
            EventTeam.event == event.key).fetch(1000, keys_only=True)
        existing_event_teams = ndb.get_multi(existing_event_teams_keys)
        existing_team_ids = set()
        for et in existing_event_teams:
            existing_team_ids.add(et.team.id())

        et_keys_to_delete = set()
        if event.year == cur_year and event.end_date is not None and event.end_date < datetime.datetime.now():
            for team_id in existing_team_ids.difference([team.key.id() for team in teams]):
                et_key_name = "{}_{}".format(event.key_name, team_id)
                et_keys_to_delete.add(ndb.Key(EventTeam, et_key_name))

        return teams, event_teams, et_keys_to_delete
