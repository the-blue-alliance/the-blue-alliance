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


class BrandHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_brand"

    def __init__(self, *args, **kw):
        super(BrandHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('brand.html', self.template_values)
