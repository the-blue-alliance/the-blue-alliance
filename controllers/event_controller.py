import logging
from collections import defaultdict
import datetime
import json
import os
import tba_config
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler
from consts.district_type import DistrictType
from consts.playoff_type import PlayoffType
from database import event_query, media_query
from database.district_query import DistrictsInYearQuery, DistrictQuery
from database.event_query import EventQuery, EventDivisionsQuery
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from helpers.team_helper import TeamHelper
from helpers.event_helper import EventHelper
from helpers.media_helper import MediaHelper

from models.event import Event
from models.match import Match
from models.sitevar import Sitevar
from models.team import Team
from template_engine import jinja2_engine


class EventList(CacheableHandler):
    """
    List all Events.
    """
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    VALID_YEARS = list(reversed(tba_config.VALID_YEARS))
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "event_list_{}_{}_{}"  # (year, explicit_year, state_prov)

    def __init__(self, *args, **kw):
        super(EventList, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, year=None, explicit_year=False):
        if year == '':
            return self.redirect("/events")

        if year:
            if not year.isdigit():
                self.abort(404)
            year = int(year)
            if year not in self.VALID_YEARS:
                self.abort(404)
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False

        state_prov = self.request.get('state_prov', None)
        if state_prov == '':
            state_prov = None

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year, explicit_year, state_prov)
        super(EventList, self).get(year, explicit_year)

    def _render(self, year=None, explicit_year=False):
        state_prov = self.request.get('state_prov', None)

        districts_future = DistrictsInYearQuery(year).fetch_async()
        all_events_future = event_query.EventListQuery(year).fetch_async()  # Needed for state_prov
        if state_prov:
            events_future = Event.query(Event.year==year, Event.state_prov==state_prov).fetch_async()
        else:
            events_future = all_events_future

        events = events_future.get_result()
        if state_prov == '' or (state_prov and not events):
            self.redirect(self.request.path, abort=True)

        EventHelper.sort_events(events)

        week_events = EventHelper.groupByWeek(events)

        districts = []  # a tuple of (district abbrev, district name)
        for district in districts_future.get_result():
            districts.append((district.abbreviation, district.display_name))
        districts = sorted(districts, key=lambda d: d[1])

        valid_state_provs = set()
        for event in all_events_future.get_result():
            if event.state_prov:
                valid_state_provs.add(event.state_prov)
        valid_state_provs = sorted(valid_state_provs)

        self.template_values.update({
            "events": events,
            "explicit_year": explicit_year,
            "selected_year": year,
            "valid_years": self.VALID_YEARS,
            "week_events": week_events,
            "districts": districts,
            "state_prov": state_prov,
            "valid_state_provs": valid_state_provs,
        })

        if year == datetime.datetime.now().year:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        return jinja2_engine.render('event_list.html', self.template_values)

    def memcacheFlush(self):
        year = datetime.datetime.now().year
        keys = [self.CACHE_KEY_FORMAT.format(year, True, None), self.CACHE_KEY_FORMAT.format(year, False, None)]
        memcache.delete_multi(keys)
        return keys


class EventDetail(CacheableHandler):
    """
    Show an Event.
    event_code like "2010ct"
    """
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 61
    CACHE_VERSION = 5
    CACHE_KEY_FORMAT = "event_detail_{}"  # (event_key)

    def __init__(self, *args, **kw):
        super(EventDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, event_key):
        if not event_key:
            return self.redirect("/events")

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(event_key)
        super(EventDetail, self).get(event_key)

    def _render(self, event_key):
        event = EventQuery(event_key).fetch()

        if not event:
            self.abort(404)

        event.prepAwardsMatchesTeams()
        event.prep_details()
        medias_future = media_query.EventTeamsPreferredMediasQuery(event_key).fetch_async()
        district_future = DistrictQuery(event.district_key.id()).fetch_async() if event.district_key else None
        event_medias_future = media_query.EventMediasQuery(event_key).fetch_async()
        status_sitevar_future = Sitevar.get_by_id_async('apistatus.down_events')

        event_divisions_future = None
        event_codivisions_future = None
        parent_event_future = None
        if event.divisions:
            event_divisions_future = ndb.get_multi_async(event.divisions)
        elif event.parent_event:
            parent_event_future = event.parent_event.get_async()
            event_codivisions_future = EventDivisionsQuery(event.parent_event.id()).fetch_async()

        awards = AwardHelper.organizeAwards(event.awards)
        cleaned_matches = MatchHelper.deleteInvalidMatches(event.matches, event)
        matches = MatchHelper.organizeMatches(cleaned_matches)
        teams = TeamHelper.sortTeams(event.teams)

        # Organize medias by team
        image_medias = MediaHelper.get_images([media for media in medias_future.get_result()])
        team_medias = defaultdict(list)
        for image_media in image_medias:
            for reference in image_media.references:
                team_medias[reference].append(image_media)
        team_and_medias = []
        for team in teams:
            team_and_medias.append((team, team_medias.get(team.key, [])))

        num_teams = len(team_and_medias)
        middle_value = num_teams / 2
        if num_teams % 2 != 0:
            middle_value += 1
        teams_a, teams_b = team_and_medias[:middle_value], team_and_medias[middle_value:]

        oprs = [i for i in event.matchstats['oprs'].items()] if (event.matchstats is not None and 'oprs' in event.matchstats) else []
        oprs = sorted(oprs, key=lambda t: t[1], reverse=True)  # sort by OPR
        oprs = oprs[:15]  # get the top 15 OPRs

        if event.now:
            matches_recent = MatchHelper.recentMatches(cleaned_matches)
            matches_upcoming = MatchHelper.upcomingMatches(cleaned_matches)
        else:
            matches_recent = None
            matches_upcoming = None

        bracket_table = event.playoff_bracket
        playoff_advancement = event.playoff_advancement
        double_elim_matches = PlayoffAdvancementHelper.getDoubleElimMatches(event, matches)
        playoff_template = PlayoffAdvancementHelper.getPlayoffTemplate(event)

        # Lazy handle the case when we haven't backfilled the event details
        if not bracket_table or not playoff_advancement:
            bracket_table2, playoff_advancement2, _, _ = PlayoffAdvancementHelper.generatePlayoffAdvancement(event, matches)
            bracket_table = bracket_table or bracket_table2
            playoff_advancement = playoff_advancement or playoff_advancement2

        district_points_sorted = None
        if event.district_key and event.district_points:
            district_points_sorted = sorted(event.district_points['points'].items(), key=lambda (team, points): -points['total'])

        event_insights = event.details.insights if event.details else None
        event_insights_template = None
        if event_insights:
            event_insights_template = 'event_partials/event_insights_{}.html'.format(event.year)

        district = district_future.get_result() if district_future else None
        event_divisions = None
        if event_divisions_future:
            event_divisions = [e.get_result() for e in event_divisions_future]
        elif event_codivisions_future:
            event_divisions = event_codivisions_future.get_result()

        medias_by_slugname = MediaHelper.group_by_slugname([media for media in event_medias_future.get_result()])
        has_time_predictions = matches_upcoming and any(match.predicted_time for match in matches_upcoming)

        status_sitevar = status_sitevar_future.get_result()

        self.template_values.update({
            "event": event,
            "event_down": status_sitevar and event_key in status_sitevar.contents,
            "district_name": district.display_name if district else None,
            "district_abbrev": district.abbreviation if district else None,
            "matches": matches,
            "matches_recent": matches_recent,
            "matches_upcoming": matches_upcoming,
            'has_time_predictions': has_time_predictions,
            "awards": awards,
            "teams_a": teams_a,
            "teams_b": teams_b,
            "num_teams": num_teams,
            "oprs": oprs,
            "bracket_table": bracket_table,
            "playoff_advancement": playoff_advancement,
            "playoff_template": playoff_template,
            "playoff_advancement_tiebreakers": PlayoffAdvancementHelper.ROUND_ROBIN_TIEBREAKERS.get(event.year),
            "district_points_sorted": district_points_sorted,
            "event_insights_qual": event_insights['qual'] if event_insights else None,
            "event_insights_playoff": event_insights['playoff'] if event_insights else None,
            "event_insights_template": event_insights_template,
            "medias_by_slugname": medias_by_slugname,
            "event_divisions": event_divisions,
            'parent_event': parent_event_future.get_result() if parent_event_future else None,
            'double_elim_matches': double_elim_matches,
            'double_elim_playoff_types': PlayoffType.DOUBLE_ELIM_TYPES,
        })

        if event.within_a_day:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        return jinja2_engine.render('event_details.html', self.template_values)


class EventInsights(CacheableHandler):
    """
    Show an Event's advanced insights.
    event_code like "2010ct"
    """
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "event_insights_{}"  # (event_key)

    def __init__(self, *args, **kw):
        super(EventInsights, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, event_key):
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(event_key)
        super(EventInsights, self).get(event_key)

    def _render(self, event_key):
        event = Event.get_by_id(event_key)

        if not event or event.year < 2016 or not event.details or not event.details.predictions:
            self.abort(404)

        event.get_matches_async()

        match_predictions = event.details.predictions.get('match_predictions', None)
        match_prediction_stats = event.details.predictions.get('match_prediction_stats', None)

        ranking_predictions = event.details.predictions.get('ranking_predictions', None)
        ranking_prediction_stats = event.details.predictions.get('ranking_prediction_stats', None)

        cleaned_matches = MatchHelper.deleteInvalidMatches(event.matches, event)
        matches = MatchHelper.organizeMatches(cleaned_matches)

        # If no matches but there are match predictions, create fake matches
        # For cases where FIRST doesn't allow posting of match schedule
        fake_matches = False
        if match_predictions and (not matches['qm'] and match_predictions['qual']):
            fake_matches = True
            for i in xrange(len(match_predictions['qual'].keys())):
                match_number = i + 1
                alliances = {
                    'red': {
                        'score': -1,
                        'teams': ['frc?', 'frc?', 'frc?']
                    },
                    'blue': {
                        'score': -1,
                        'teams': ['frc?', 'frc?', 'frc?']
                    }
                }
                matches['qm'].append(Match(
                    id=Match.renderKeyName(
                        event_key,
                        'qm',
                        1,
                        match_number),
                    event=event.key,
                    year=event.year,
                    set_number=1,
                    match_number=match_number,
                    comp_level='qm',
                    alliances_json=json.dumps(alliances),
                ))

        # Add actual scores to predictions
        distribution_info = {}
        for comp_level in Match.COMP_LEVELS:
            level = 'qual' if comp_level == 'qm' else 'playoff'
            for match in matches[comp_level]:
                distribution_info[match.key.id()] = {
                    'level': level,
                    'red_actual_score': match.alliances['red']['score'],
                    'blue_actual_score': match.alliances['blue']['score'],
                    'red_mean': match_predictions[level][match.key.id()]['red']['score'],
                    'blue_mean': match_predictions[level][match.key.id()]['blue']['score'],
                    'red_var': match_predictions[level][match.key.id()]['red']['score_var'],
                    'blue_var': match_predictions[level][match.key.id()]['blue']['score_var'],
            }

        last_played_match_num = None
        if ranking_prediction_stats:
            last_played_match_key = ranking_prediction_stats.get('last_played_match', None)
            if last_played_match_key:
                last_played_match_num = last_played_match_key.split('_qm')[1]

        self.template_values.update({
            "event": event,
            "matches": matches,
            "fake_matches": fake_matches,
            "match_predictions": match_predictions,
            "distribution_info_json": json.dumps(distribution_info),
            "match_prediction_stats": match_prediction_stats,
            "ranking_predictions": ranking_predictions,
            "ranking_prediction_stats": ranking_prediction_stats,
            "last_played_match_num": last_played_match_num,
        })

        if event.within_a_day:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        return jinja2_engine.render('event_insights.html', self.template_values)


class EventRss(CacheableHandler):
    """
    Generates a RSS feed for the matches in a event
    """
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "event_rss_{}"  # (event_key)

    def __init__(self, *args, **kw):
        super(EventRss, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 5

    def get(self, event_key):
        if not event_key:
            return self.redirect("/events")

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(event_key)
        super(EventRss, self).get(event_key)

    def _render(self, event_key):
        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)

        matches = MatchHelper.organizeMatches(event.matches)

        self.template_values.update({
            "event": event,
            "matches": matches,
            "datetime": datetime.datetime.now()
        })

        self.response.headers['content-type'] = 'application/xml; charset=UTF-8'
        return jinja2_engine.render('event_rss.xml', self.template_values)


class EventNextMatchHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "next_match"

    def __init__(self, *args, **kw):
        super(EventNextMatchHandler, self).__init__(*args, **kw)
        self._cache_expiration = 61

    def _render(self, event_key):
        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)
            return
        medias_future = media_query.EventTeamsPreferredMediasQuery(event_key).fetch_async()
        next_match = MatchHelper.upcomingMatches(event.matches, num=1)
        next_match = next_match[0] if next_match else None
        team_and_medias = []
        if next_match:
            # Organize medias by team
            teams = ndb.get_multi([ndb.Key(Team, team_key) for team_key in next_match.alliances['red']['teams'] + next_match.alliances['blue']['teams']])
            image_medias = MediaHelper.get_images([media for media in medias_future.get_result()])
            team_medias = defaultdict(list)
            for image_media in image_medias:
                for reference in image_media.references:
                    team_medias[reference].append(image_media)

            stations = ['Red 1', 'Red 2', 'Red 3', 'Blue 1', 'Blue 2', 'Blue 3']
            for i, team in enumerate(teams):
                team_and_medias.append((team, stations[i], team_medias.get(team.key, [])))

        self.template_values.update({
            'event': event,
            'next_match': next_match,
            'teams_and_media': team_and_medias,
        })
        return jinja2_engine.render('nextmatch.html', self.template_values)
