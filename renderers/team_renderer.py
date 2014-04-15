import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher

from helpers.award_helper import AwardHelper
from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.media_helper import MediaHelper

from models.award import Award
from models.event_team import EventTeam
from models.match import Match
from models.media import Media


class TeamRenderer(object):
    @classmethod
    def render_team_details(cls, handler, team, year, is_canonical):
        media_key_futures = Media.query(Media.references == team.key, Media.year == year).fetch_async(500, keys_only=True)
        events_sorted, matches_by_event_key, awards_by_event_key, valid_years = TeamDetailsDataFetcher.fetch(team, year, return_valid_years=True)
        if not events_sorted:
            return None

        media_futures = ndb.get_multi_async(media_key_futures.get_result())

        participation = []
        year_wlt_list = []

        current_event = None
        matches_upcoming = None
        short_cache = False
        for event in events_sorted:
            event_matches = matches_by_event_key.get(event.key, [])
            event_awards = AwardHelper.organizeAwards(awards_by_event_key.get(event.key, []))
            matches_organized = MatchHelper.organizeMatches(event_matches)

            if event.now:
                current_event = event
                matches_upcoming = MatchHelper.upcomingMatches(event_matches)

            if event.within_a_day:
                short_cache = True

            wlt = EventHelper.calculateTeamWLTFromMatches(team.key_name, event_matches)
            year_wlt_list.append(wlt)
            if wlt["win"] + wlt["loss"] + wlt["tie"] == 0:
                display_wlt = None
            else:
                display_wlt = wlt

            team_rank = None
            if event.rankings:
                for element in event.rankings:
                    if element[1] == str(team.team_number):
                        team_rank = element[0]
                        break

            participation.append({'event': event,
                                   'matches': matches_organized,
                                   'wlt': display_wlt,
                                   'rank': team_rank,
                                   'awards': event_awards})

        year_wlt = {"win": 0, "loss": 0, "tie": 0}
        for wlt in year_wlt_list:
            year_wlt["win"] += wlt["win"]
            year_wlt["loss"] += wlt["loss"]
            year_wlt["tie"] += wlt["tie"]
        if year_wlt["win"] + year_wlt["loss"] + year_wlt["tie"] == 0:
            year_wlt = None

        medias_by_slugname = MediaHelper.group_by_slugname([media_future.get_result() for media_future in media_futures])
        image_medias = MediaHelper.get_images([media_future.get_result() for media_future in media_futures])

        template_values = {"is_canonical": is_canonical,
                           "team": team,
                           "participation": participation,
                           "year": year,
                           "years": valid_years,
                           "year_wlt": year_wlt,
                           "current_event": current_event,
                           "matches_upcoming": matches_upcoming,
                           "medias_by_slugname": medias_by_slugname,
                           "image_medias":image_medias}

        if short_cache:
            handler._cache_expiration = handler.SHORT_CACHE_EXPIRATION

        path = os.path.join(os.path.dirname(__file__), '../templates/team_details.html')
        return template.render(path, template_values)

    @classmethod
    def render_team_history(cls, handler, team, is_canonical):
        event_team_keys_future = EventTeam.query(EventTeam.team == team.key).fetch_async(1000, keys_only=True)
        award_keys_future = Award.query(Award.team_list == team.key).fetch_async(1000, keys_only=True)

        event_teams_futures = ndb.get_multi_async(event_team_keys_future.get_result())
        awards_futures = ndb.get_multi_async(award_keys_future.get_result())

        event_keys = [event_team_future.get_result().event for event_team_future in event_teams_futures]
        events_futures = ndb.get_multi_async(event_keys)

        awards_by_event = {}
        for award_future in awards_futures:
            award = award_future.get_result()
            if award.event.id() not in awards_by_event:
                awards_by_event[award.event.id()] = [award]
            else:
                awards_by_event[award.event.id()].append(award)

        event_awards = []
        current_event = None
        matches_upcoming = None
        short_cache = False
        for event_future in events_futures:
            event = event_future.get_result()
            if event.now:
                current_event = event

                team_matches_future = Match.query(Match.event == event.key, Match.team_key_names == team.key_name)\
                  .fetch_async(500, keys_only=True)
                matches = ndb.get_multi(team_matches_future.get_result())
                matches_upcoming = MatchHelper.upcomingMatches(matches)

            if event.within_a_day:
                short_cache = True

            if event.key_name in awards_by_event:
                sorted_awards = AwardHelper.organizeAwards(awards_by_event[event.key_name])
            else:
                sorted_awards = []
            event_awards.append((event, sorted_awards))
        event_awards = sorted(event_awards, key=lambda (e, _): e.start_date if e.start_date else datetime.datetime(e.year, 12, 31))

        years = sorted(set([et.get_result().year for et in event_teams_futures if et.get_result().year is not None]))

        template_values = {'is_canonical': is_canonical,
                           'team': team,
                           'event_awards': event_awards,
                           'years': years,
                           'current_event': current_event,
                           'matches_upcoming': matches_upcoming}

        if short_cache:
            handler._cache_expiration = handler.SHORT_CACHE_EXPIRATION

        path = os.path.join(os.path.dirname(__file__), '../templates/team_history.html')
        return template.render(path, template_values)
