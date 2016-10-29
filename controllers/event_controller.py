from collections import defaultdict
import datetime
import json
import os
import tba_config

from google.appengine.api import memcache, search
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler
from consts.district_type import DistrictType
from database import event_query, media_query
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from helpers.team_helper import TeamHelper
from helpers.event_helper import EventHelper
from helpers.event_insights_helper import EventInsightsHelper
from helpers.media_helper import MediaHelper

from models.event import Event
from models.match import Match
from template_engine import jinja2_engine

from consts.ranking_indexes import RankingIndexes


class EventList(CacheableHandler):
    """
    List all Events.
    """
    VALID_YEARS = list(reversed(range(1992, tba_config.MAX_YEAR + 1)))
    VALID_RANGES = [10, 50, 100, 500]  # in km
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "event_list_{}_{}"  # (year, explicit_year)

    def __init__(self, *args, **kw):
        super(EventList, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

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

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year, explicit_year)
        super(EventList, self).get(year, explicit_year)

    def _render(self, year=None, explicit_year=False):
        state_prov = self.request.get('state_prov', None)
        postalcode = self.request.get('postalcode', None)
        range_km = self.request.get('range', None)
        if range_km and range_km.isdigit():
            range_km = int(range_km)
        else:
            range_km = self.VALID_YEARS[0]
        if postalcode:
            lat_lon_future = EventHelper.get_lat_lon_async(postalcode)

        all_events_future = event_query.EventListQuery(year).fetch_async()  # Needed for valid city/state_prov/country
        if not state_prov:
            events_future = all_events_future
        else:
            events_future = Event.query(Event.year==year, Event.state_prov==state_prov).fetch_async()

        # Filter events by range
        if postalcode:
            if lat_lon_future.get_result():
                lat, lon = lat_lon_future.get_result()
                query_string = "distance(location, geopoint({}, {})) < {} AND year={}".format(lat, lon, range_km * 1000, year)
                events_in_range = set([result.doc_id for result in search.Index(name="eventLocation").search(query_string).results])

                events = filter(lambda e: e.key.id() in events_in_range, events_future.get_result())
            else:
                events = []
        else:
            events = events_future.get_result()

        EventHelper.sort_events(events)

        week_events = EventHelper.groupByWeek(events)

        district_enums = set()
        for event in events:
            if event.event_district_enum is not None and event.event_district_enum != DistrictType.NO_DISTRICT:
                district_enums.add(event.event_district_enum)

        districts = []  # a tuple of (district abbrev, district name)
        for district_enum in district_enums:
            districts.append((DistrictType.type_abbrevs[district_enum],
                              DistrictType.type_names[district_enum]))
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
            "postalcode": postalcode,
            "range": range_km,
            "valid_state_provs": valid_state_provs,
            "valid_ranges": self.VALID_RANGES,
        })

        return jinja2_engine.render('event_list.html', self.template_values)

    def memcacheFlush(self):
        year = datetime.datetime.now().year
        keys = [self.CACHE_KEY_FORMAT.format(year, True), self.CACHE_KEY_FORMAT.format(year, False)]
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
        event = Event.get_by_id(event_key)

        if not event:
            self.abort(404)

        event.prepAwardsMatchesTeams()
        medias_future = media_query.EventTeamsPreferredMediasQuery(event_key).fetch_async()

        awards = AwardHelper.organizeAwards(event.awards)
        cleaned_matches = MatchHelper.deleteInvalidMatches(event.matches)
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

        bracket_table = MatchHelper.generateBracket(matches, event.alliance_selections)
        is_2015_playoff = EventHelper.is_2015_playoff(event_key)
        if is_2015_playoff:
            playoff_advancement = MatchHelper.generatePlayoffAdvancement2015(matches, event.alliance_selections)
            for comp_level in ['qf', 'sf']:
                if comp_level in bracket_table:
                    del bracket_table[comp_level]
        else:
            playoff_advancement = None

        district_points_sorted = None
        if event.district_points:
            district_points_sorted = sorted(event.district_points['points'].items(), key=lambda (team, points): -points['total'])

        event_insights = EventInsightsHelper.calculate_event_insights(cleaned_matches, event.year)
        event_insights_template = None
        if event_insights:
            event_insights_template = 'event_partials/event_insights_{}.html'.format(event.year)

        # rankings processing for ranking score per match
        full_rankings = event.rankings
        rankings_enhanced = event.rankings_enhanced
        if rankings_enhanced is not None:
            rp_index = RankingIndexes.CUMULATIVE_RANKING_SCORE[event.year]
            matches_index = RankingIndexes.MATCHES_PLAYED[event.year]
            ranking_criterion_name = full_rankings[0][rp_index]
            full_rankings[0].append(ranking_criterion_name + "/Match*")

            for row in full_rankings[1:]:
                team = row[1]
                if rankings_enhanced["ranking_score_per_match"] is not None:
                    rp_per_match = rankings_enhanced['ranking_score_per_match'][team]
                    row.append(rp_per_match)
                if rankings_enhanced["match_offset"] is not None:
                    match_offset = rankings_enhanced["match_offset"][team]
                    if match_offset != 0:
                        row[matches_index] = "{} ({})".format(row[matches_index], match_offset)

        self.template_values.update({
            "event": event,
            "district_name": DistrictType.type_names.get(event.event_district_enum, None),
            "district_abbrev": DistrictType.type_abbrevs.get(event.event_district_enum, None),
            "matches": matches,
            "matches_recent": matches_recent,
            "matches_upcoming": matches_upcoming,
            "awards": awards,
            "teams_a": teams_a,
            "teams_b": teams_b,
            "num_teams": num_teams,
            "oprs": oprs,
            "bracket_table": bracket_table,
            "playoff_advancement": playoff_advancement,
            "district_points_sorted": district_points_sorted,
            "is_2015_playoff": is_2015_playoff,
            "event_insights_qual": event_insights['qual'] if event_insights else None,
            "event_insights_playoff": event_insights['playoff'] if event_insights else None,
            "event_insights_template": event_insights_template,
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

        if not event or event.year != 2016:
            self.abort(404)

        event.get_matches_async()

        match_predictions = event.details.predictions.get('match_predictions', None)
        match_prediction_stats = event.details.predictions.get('match_prediction_stats', None)

        ranking_predictions = event.details.predictions.get('ranking_predictions', None)
        ranking_prediction_stats = event.details.predictions.get('ranking_prediction_stats', None)

        cleaned_matches = MatchHelper.deleteInvalidMatches(event.matches)
        matches = MatchHelper.organizeMatches(cleaned_matches)

        # If no matches but there are match predictions, create fake matches
        # For cases where FIRST doesn't allow posting of match schedule
        fake_matches = False
        if not matches['qm'] and match_predictions:
            fake_matches = True
            for i in xrange(len(match_predictions.keys())):
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
