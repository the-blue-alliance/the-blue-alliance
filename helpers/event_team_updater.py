import datetime

from google.appengine.ext import ndb

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
        An EventTeam is valid iff the team played a match at the event or
        the event has not yet occurred.
        """
        event = Event.get_by_id(event_key)

        # Add teams from Matches
        team_ids = set()
        match_keys = Match.query(
            Match.event == event.key).fetch(1000, keys_only=True)
        matches = ndb.get_multi(match_keys)
        for match in matches:
            for team in match.team_key_names:
                team_ids.add(team)

        # Create or update EventTeams
        teams = [Team(id=team_id,
                      team_number=int(team_id[3:]))
                      for team_id in team_ids]

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
        if event.end_date < datetime.datetime.now():
            for team_id in existing_team_ids.difference(team_ids):
                et_key_name = "{}_{}".format(event.key_name, team_id)
                et_keys_to_delete.add(ndb.Key(EventTeam, et_key_name))
            ndb.delete_multi(et_keys_to_delete)

        return teams, event_teams, et_keys_to_delete
