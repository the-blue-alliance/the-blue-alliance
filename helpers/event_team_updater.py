import datetime

from google.appengine.ext import ndb

from helpers.match_helper import MatchHelper
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
        e) the winning alliance of one of this event's divisions
        f) or the event is not from the current year. (This is to make sure we don't delete old data we may no longer be able to scrape)
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

        division_futures = ndb.get_multi_async(event.divisions) if event.divisions else []
        division_matches_futures = [Match.query(
            Match.event == division).fetch_async(1000) for division in event.divisions] if event.divisions else []

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

        # Add teams from division winners
        if division_futures and division_matches_futures:
            for division_future, matches_future in zip(division_futures, division_matches_futures):
                division_winners = self.get_event_winners(division_future.get_result(), matches_future.get_result())
                team_ids = team_ids.union(division_winners)

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

    @classmethod
    def get_event_winners(cls, event, matches):
        """
        First alliance to win two finals matches is the winner
        """
        matches_by_type = MatchHelper.organizeMatches(matches)
        if 'f' not in matches_by_type or not matches_by_type['f']:
            return set()
        finals_matches = matches_by_type['f']
        red_wins = 0
        blue_wins = 0
        for match in finals_matches:
            if match.has_been_played:
                if match.winning_alliance == 'red':
                    red_wins += 1
                elif match.winning_alliance == 'blue':
                    blue_wins += 1

        winning_teams = set()
        if red_wins >= 2:
            winning_teams = set(finals_matches[0].alliances['red']['teams'])
        elif blue_wins >= 2:
            winning_teams = set(finals_matches[0].alliances['blue']['teams'])

        # Return the entire alliance
        alliance_selections = event.alliance_selections
        if alliance_selections:
            for alliance in alliance_selections:
                if len(winning_teams.intersection(set(alliance['picks']))) >= 2:
                    complete_alliance = set(alliance['picks']) if alliance else set()
                    if alliance and alliance.get('backup'):
                        complete_alliance.add(alliance['backup']['in'])
                    return complete_alliance

        # Fall back to the match winners
        return winning_teams
