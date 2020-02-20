from collections import defaultdict
import datetime
import logging

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import ndb

import tba_config
from base_controller import CacheableHandler
from consts.award_type import AwardType
from consts.event_type import EventType
from consts.landing_type import LandingType
from consts.media_tag import MediaTag
from consts.media_type import MediaType
from database import media_query
from helpers.event_helper import EventHelper
from helpers.season_helper import SeasonHelper
from helpers.team_helper import TeamHelper
from helpers.firebase.firebase_pusher import FirebasePusher
from models.award import Award
from models.event import Event
from models.insight import Insight
from models.media import Media
from models.team import Team
from models.sitevar import Sitevar
from template_engine import jinja2_engine


def render_static(page):
    memcache_key = "main_%s" % page
    html = memcache.get(memcache_key)

    if html is None:
        html = jinja2_engine.render('%s.html' % page, {})
        if tba_config.CONFIG["memcache"]:
            memcache.set(memcache_key, html, 86400)

    return html


def handle_404(request, response, exception):
    response.write(render_static("404"))
    response.set_status(404)


def handle_500(request, response, exception):
    logging.exception(exception)
    response.write(render_static("500"))
    response.set_status(500)


class AvatarsHandler(CacheableHandler):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "avatars_{}"

    def __init__(self, *args, **kw):
        super(AvatarsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def get(self, year):
        year = int(year)
        if year not in {2018, 2019, 2020}:
            self.abort(404)

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year)
        super(AvatarsHandler, self).get(year)

    def _render(self, year):
        year = int(year)
        avatars = []
        shards = memcache.get_multi(['{}avatars_{}'.format(year, i) for i in xrange(10)])
        if len(shards) == 10:  # If missing a shard, must refetch all
            for _, shard in sorted(shards.items(), key=lambda kv: kv[0]):
                avatars += shard

        if not avatars:
            avatars_future = Media.query(Media.media_type_enum == MediaType.AVATAR, Media.year == year).fetch_async()
            avatars = sorted(avatars_future.get_result(), key=lambda a: int(a.references[0].id()[3:]))

            shards = {}
            size = len(avatars) / 10 + 1
            for i in xrange(10):
                start = i * size
                end = start + size
                shards['{}avatars_{}'.format(year, i)] = avatars[start:end]
            memcache.set_multi(shards, 60*60*24)

        self.template_values.update({
            'year': year,
            'avatars': avatars,
        })
        return jinja2_engine.render('avatars.html', self.template_values)


class TwoChampsHandler(CacheableHandler):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "two_champs_{}_{}"

    def __init__(self, *args, **kw):
        super(TwoChampsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24
        self._team_key_a = self.request.get('team_a', None)
        self._team_key_b = self.request.get('team_b', None)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self._team_key_a, self._team_key_b)

    def _render(self, *args, **kw):
        team_a = Team.get_by_id(self._team_key_a) if self._team_key_a else None
        team_b = Team.get_by_id(self._team_key_b) if self._team_key_b else None
        self.template_values.update({
            'team_a': team_a,
            'team_b': team_b,
        })
        return jinja2_engine.render('2champs.html', self.template_values)


class MainKickoffHandler(CacheableHandler):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "main_kickoff"

    def __init__(self, *args, **kw):
        super(MainKickoffHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _render(self, *args, **kw):
        special_webcasts = FirebasePusher.get_special_webcasts()
        effective_season_year = SeasonHelper.effective_season_year()

        self.template_values.update({
            'events': EventHelper.getWeekEvents(),
            'is_kickoff': SeasonHelper.is_kickoff_at_least_one_day_away(year=effective_season_year),
            'kickoff_datetime_est': SeasonHelper.kickoff_datetime_est(effective_season_year),
            'kickoff_datetime_utc': SeasonHelper.kickoff_datetime_utc(effective_season_year),
            "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
            "special_webcasts": special_webcasts,
        })

        return jinja2_engine.render('index/index_kickoff.html', self.template_values)


class MainBuildseasonHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_buildseason"

    def __init__(self, *args, **kw):
        super(MainBuildseasonHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 5

    def _render(self, *args, **kw):
        effective_season_year = SeasonHelper.effective_season_year()
        special_webcasts = FirebasePusher.get_special_webcasts()

        self.template_values.update({
            'seasonstart_datetime_utc': SeasonHelper.first_event_datetime_utc(effective_season_year),
            'events': EventHelper.getWeekEvents(),
            "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
            "special_webcasts": special_webcasts,
        })

        return jinja2_engine.render('index/index_buildseason.html', self.template_values)


class MainChampsHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_champs"

    def __init__(self, *args, **kw):
        super(MainChampsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 5

    def _render(self, *args, **kw):
        year = datetime.datetime.now().year
        hou_event_keys_future = Event.query(
            Event.year == year,
            Event.event_type_enum.IN(EventType.CMP_EVENT_TYPES),
            Event.start_date <= datetime.datetime(2019, 4, 21)).fetch_async(keys_only=True)
        det_event_keys_future = Event.query(
            Event.year == year,
            Event.event_type_enum.IN(EventType.CMP_EVENT_TYPES),
            Event.start_date > datetime.datetime(2019, 4, 21)).fetch_async(keys_only=True)

        hou_events_futures = ndb.get_multi_async(hou_event_keys_future.get_result())
        det_events_futures = ndb.get_multi_async(det_event_keys_future.get_result())

        self.template_values.update({
            "hou_events": [e.get_result() for e in hou_events_futures],
            "det_events": [e.get_result() for e in det_events_futures],
            "year": year,
        })

        return jinja2_engine.render('index/index_champs.html', self.template_values)


class MainCompetitionseasonHandler(CacheableHandler):
    CACHE_VERSION = 5
    CACHE_KEY_FORMAT = "main_competitionseason"

    def __init__(self, *args, **kw):
        super(MainCompetitionseasonHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 5

    def _render(self, *args, **kw):
        week_events = EventHelper.getWeekEvents()
        popular_teams_events = TeamHelper.getPopularTeamsEvents(week_events)

        # Only show special webcasts that aren't also hosting an event
        special_webcasts = []
        for special_webcast in FirebasePusher.get_special_webcasts():
            add = True
            for event in week_events:
                if event.now and event.webcast:
                    for event_webcast in event.webcast:
                        if (special_webcast.get('type', '') == event_webcast.get('type', '') and
                                special_webcast.get('channel', '') == event_webcast.get('channel', '') and
                                special_webcast.get('file', '') == event_webcast.get('file', '')):
                            add = False
                            break
                if not add:
                    break
            if add:
                special_webcasts.append(special_webcast)

        self.template_values.update({
            "events": week_events,
            "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
            "special_webcasts": special_webcasts,
            "popular_teams_events": popular_teams_events,
        })

        return jinja2_engine.render('index/index_competitionseason.html', self.template_values)


class MainInsightsHandler(CacheableHandler):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "main_insights"

    def __init__(self, *args, **kw):
        super(MainInsightsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 5

    def _render(self, *args, **kw):
        week_events = EventHelper.getWeekEvents()
        year = datetime.datetime.now().year
        special_webcasts = FirebasePusher.get_special_webcasts()
        self.template_values.update({
            "events": week_events,
            "year": year,
            "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
            "special_webcasts": special_webcasts,
        })

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(year, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        for insight in insights:
            if insight:
                self.template_values[insight.name] = insight

        return jinja2_engine.render('index/index_insights.html', self.template_values)


class MainOffseasonHandler(CacheableHandler):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "main_offseason"

    def __init__(self, *args, **kw):
        super(MainOffseasonHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _render(self, *args, **kw):
        special_webcasts = FirebasePusher.get_special_webcasts()
        effective_season_year = SeasonHelper.effective_season_year()

        self.template_values.update({
            "events": EventHelper.getWeekEvents(),
            'kickoff_datetime_utc': SeasonHelper.kickoff_datetime_utc(effective_season_year),
            "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
            "special_webcasts": special_webcasts,
        })

        return jinja2_engine.render('index/index_offseason.html', self.template_values)


class MainLandingHandler(CacheableHandler):

    CACHE_VERSION = None
    CACHE_KEY_FORMAT = None

    HANDLER_MAP = {LandingType.KICKOFF: MainKickoffHandler,
                   LandingType.BUILDSEASON: MainBuildseasonHandler,
                   LandingType.CHAMPS: MainChampsHandler,
                   LandingType.COMPETITIONSEASON: MainCompetitionseasonHandler,
                   LandingType.OFFSEASON: MainOffseasonHandler,
                   LandingType.INSIGHTS: MainInsightsHandler,
                  }

    def __init__(self, *args, **kw):
        super(MainLandingHandler, self).__init__(*args, **kw)
        config_sitevar = Sitevar.get_by_id('landing_config')
        handler = None
        if config_sitevar:
            self.template_values.update(config_sitevar.contents)
            handler_type = config_sitevar.contents.get('current_landing')
            handler = self.HANDLER_MAP.get(handler_type, None)
        if not handler:
            # Default to build season handler
            handler = MainBuildseasonHandler

        self.handler_instance = handler()
        self._cache_expiration = self.handler_instance._cache_expiration
        self._partial_cache_key = self.handler_instance._partial_cache_key

    def _render(self, *args, **kw):
        self.handler_instance.template_values = self.template_values
        return self.handler_instance._render(*args, **kw)


class ContactHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_contact"

    def __init__(self, *args, **kw):
        super(ContactHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('contact.html', self.template_values)


class PrivacyHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_privacy"

    def __init__(self, *args, **kw):
        super(PrivacyHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('privacy.html', self.template_values)


class HashtagsHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_hashtags"

    def __init__(self, *args, **kw):
        super(HashtagsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('hashtags.html', self.template_values)


class FIRSTHOFHandler(CacheableHandler):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "main_first_hof"

    def __init__(self, *args, **kw):
        super(FIRSTHOFHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        awards_future = Award.query(
            Award.award_type_enum==AwardType.CHAIRMANS,
            Award.event_type_enum==EventType.CMP_FINALS).fetch_async()

        teams_by_year = defaultdict(list)
        for award in awards_future.get_result():
            for team_key in award.team_list:
                teams_by_year[award.year].append((
                    team_key.get_async(),
                    award.event.get_async(),
                    award,
                    media_query.TeamTagMediasQuery(team_key.id(), MediaTag.CHAIRMANS_VIDEO).fetch_async(),
                    media_query.TeamTagMediasQuery(team_key.id(), MediaTag.CHAIRMANS_PRESENTATION).fetch_async(),
                    media_query.TeamTagMediasQuery(team_key.id(), MediaTag.CHAIRMANS_ESSAY).fetch_async(),
                ))

        teams_by_year = sorted(teams_by_year.items(), key=lambda (k, v): -k)
        for _, tea in teams_by_year:
            tea.sort(key=lambda x: x[1].get_result().start_date)

        self.template_values.update({
            'teams_by_year': teams_by_year,
        })

        return jinja2_engine.render('hof.html', self.template_values)


class AboutHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_about"

    def __init__(self, *args, **kw):
        super(AboutHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('about.html', self.template_values)


class ThanksHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_thanks"

    def __init__(self, *args, **kw):
        super(ThanksHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('thanks.html', self.template_values)


class OprHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_opr"

    def __init__(self, *args, **kw):
        super(OprHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('opr.html', self.template_values)


class PredictionsHandler(CacheableHandler):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "main_predictions"

    def __init__(self, *args, **kw):
        super(PredictionsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('predictions.html', self.template_values)


class SearchHandler(webapp2.RequestHandler):
    def get(self):
        try:
            q = self.request.get("q")
            logging.info("search query: %s" % q)
            if q.isdigit():
                team_id = "frc%s" % int(q)
                team = Team.get_by_id(team_id)
                if team:
                    self.redirect(team.details_url)
                    return None
            elif q[:4].isdigit():  # Check for event key
                event = Event.get_by_id(q)
                if event:
                    self.redirect(event.details_url)
                    return None
            else:  # Check for event short
                year = datetime.datetime.now().year  # default to current year
                event = Event.get_by_id('{}{}'.format(year, q))
                if event:
                    self.redirect(event.details_url)
                    return None
        except Exception, e:
            logging.warning("warning: %s" % e)
        finally:
            self.response.out.write(render_static("search"))


class WebcastsHandler(CacheableHandler):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "main_webcasts"

    def __init__(self, *args, **kw):
        super(WebcastsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        year = datetime.datetime.now().year
        event_keys = Event.query(Event.year == year).order(Event.start_date).fetch(500, keys_only=True)
        events = ndb.get_multi(event_keys)

        self.template_values.update({
            'events': events,
            'year': year,
        })

        return jinja2_engine.render('webcasts.html', self.template_values)


class ApiWriteHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "api_write"

    def __init__(self, *args, **kw):
        super(ApiWriteHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('apiwrite.html', self.template_values)
