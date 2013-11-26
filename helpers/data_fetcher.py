import logging

from google.appengine.ext import ndb

from  models.award import Award
from  models.event import Event
from  models.event_team import EventTeam
from  models.match import Match


class DataFetcher(object):
    @classmethod
    def fetch_team_data(self, team, year, return_valid_years=False):
        """
        returns: events_sorted, matches_by_event_key, awards_by_event_key, valid_years
        of a team for a given year
        """
        @ndb.tasklet
        def get_events_and_matches_async():
            if return_valid_years:
                event_team_keys_query = EventTeam.query(EventTeam.team == team.key)
            else:
                event_team_keys_query = EventTeam.query(EventTeam.team == team.key, EventTeam.year == year)
            event_team_keys = yield event_team_keys_query.fetch_async(1000, keys_only=True)
            event_teams = yield ndb.get_multi_async(event_team_keys)
            event_keys = []
            for event_team in event_teams:
                if return_valid_years:
                    valid_years.add(event_team.year)  # valid_years is a "global" variable (defined below). Doing this removes the complexity of having to propagate the years up through the tasklet call chain.
                if not return_valid_years or event_team.year == year:
                    event_keys.append(event_team.event)
            events, matches = yield ndb.get_multi_async(event_keys), get_matches_async(event_keys)
            raise ndb.Return((events, matches))

        @ndb.tasklet
        def get_matches_async(event_keys):
            if event_keys == []:
                raise ndb.Return([])
            match_keys = yield Match.query(
                Match.event.IN(event_keys), Match.team_key_names == team.key_name).fetch_async(500, keys_only=True)
            matches = yield ndb.get_multi_async(match_keys)
            raise ndb.Return(matches)

        @ndb.tasklet
        def get_awards_async():
            award_keys = yield Award.query(Award.year == year, Award.team_list == team.key).fetch_async(500, keys_only=True)
            awards = yield ndb.get_multi_async(award_keys)
            raise ndb.Return(awards)

        @ndb.toplevel
        def get_events_matches_awards():
            (events, matches), awards = yield get_events_and_matches_async(), get_awards_async()
            raise ndb.Return(events, matches, awards)

        valid_years = set()
        events, matches, awards = get_events_matches_awards()
        valid_years = sorted(valid_years)

        events_sorted = sorted(events, key=lambda e: e.start_date if e.start_date else datetime.datetime(year, 12, 31))  # unknown goes last

        matches_by_event_key = {}
        for match in matches:
            if match.event in matches_by_event_key:
                matches_by_event_key[match.event].append(match)
            else:
                matches_by_event_key[match.event] = [match]
        awards_by_event_key = {}
        for award in awards:
            if award.event in awards_by_event_key:
                awards_by_event_key[award.event].append(award)
            else:
                awards_by_event_key[award.event] = [award]

        return events_sorted, matches_by_event_key, awards_by_event_key, valid_years
