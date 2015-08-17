import datetime

from google.appengine.ext import ndb

from database import award_query, event_query, match_query, team_query


class TeamDetailsDataFetcher(object):
    @classmethod
    def fetch(self, team, year, return_valid_years=False):
        """
        returns: events_sorted, matches_by_event_key, awards_by_event_key, valid_years
        of a team for a given year
        """
        awards_future = award_query.TeamYearAwardsQuery(team.key.id(), year).fetch_async()
        events_future = event_query.TeamYearEventsQuery(team.key.id(), year).fetch_async()
        matches_future = match_query.TeamYearMatchesQuery(team.key.id(), year).fetch_async()
        if return_valid_years:
            valid_years_future = team_query.TeamParticipationQuery(team.key.id()).fetch_async()

        events_sorted = sorted(events_future.get_result(), key=lambda e: e.start_date if e.start_date else datetime.datetime(year, 12, 31))  # unknown goes last

        matches_by_event_key = {}
        for match in matches_future.get_result():
            if match.event in matches_by_event_key:
                matches_by_event_key[match.event].append(match)
            else:
                matches_by_event_key[match.event] = [match]
        awards_by_event_key = {}
        for award in awards_future.get_result():
            if award.event in awards_by_event_key:
                awards_by_event_key[award.event].append(award)
            else:
                awards_by_event_key[award.event] = [award]

        if return_valid_years:
            valid_years = sorted(valid_years_future.get_result())
        else:
            valid_years = []

        return events_sorted, matches_by_event_key, awards_by_event_key, valid_years
