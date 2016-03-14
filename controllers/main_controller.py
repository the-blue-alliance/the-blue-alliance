import os
import logging
import datetime
import webapp2

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

import tba_config

from base_controller import CacheableHandler
from consts.event_type import EventType
from consts.notification_type import NotificationType
from helpers.event_helper import EventHelper

from models.event import Event
from models.insight import Insight
from models.team import Team
from models.sitevar import Sitevar


def render_static(page):
    memcache_key = "main_%s" % page
    html = memcache.get(memcache_key)

    if html is None:
        path = os.path.join(os.path.dirname(__file__), "../templates/%s.html" % page)
        html = template.render(path, {})
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


class MainKickoffHandler(CacheableHandler):
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "main_kickoff"

    def __init__(self, *args, **kw):
        super(MainKickoffHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _render(self, *args, **kw):
        kickoff_datetime_est = datetime.datetime(2016, 1, 9, 10, 30)
        kickoff_datetime_utc = kickoff_datetime_est + datetime.timedelta(hours=5)

        is_kickoff = datetime.datetime.now() >= kickoff_datetime_est - datetime.timedelta(days=1)  # turn on 1 day before

        self.template_values.update({
            'is_kickoff': is_kickoff,
            'kickoff_datetime_est': kickoff_datetime_est,
            'kickoff_datetime_utc': kickoff_datetime_utc,
        })

        path = os.path.join(os.path.dirname(__file__), "../templates/index_kickoff.html")
        return template.render(path, self.template_values)


class MainBuildseasonHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_buildseason"

    def __init__(self, *args, **kw):
        super(MainBuildseasonHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        endbuild_datetime_est = datetime.datetime(2016, 2, 23, 23, 59)
        endbuild_datetime_utc = endbuild_datetime_est + datetime.timedelta(hours=5)
        week_events = EventHelper.getWeekEvents()

        self.template_values.update({
            'endbuild_datetime_est': endbuild_datetime_est,
            'endbuild_datetime_utc': endbuild_datetime_utc,
            'events': week_events,
        })

        path = os.path.join(os.path.dirname(__file__), "../templates/index_buildseason.html")
        return template.render(path, self.template_values)


class MainChampsHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_champs"

    def __init__(self, *args, **kw):
        super(MainChampsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _render(self, *args, **kw):
        year = datetime.datetime.now().year
        event_keys = Event.query(Event.year == year, Event.event_type_enum.IN(EventType.CMP_EVENT_TYPES)).fetch(100, keys_only=True)
        events = [event_key.get() for event_key in event_keys]

        self.template_values.update({
            "events": events,
            "year": year,
        })

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(year, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        for insight in insights:
            if insight:
                self.template_values[insight.name] = insight

        path = os.path.join(os.path.dirname(__file__), '../templates/index_champs.html')
        return template.render(path, self.template_values)


class MainCompetitionseasonHandler(CacheableHandler):
    CACHE_VERSION = 5
    CACHE_KEY_FORMAT = "main_competitionseason"

    def __init__(self, *args, **kw):
        super(MainCompetitionseasonHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60

    def _render(self, *args, **kw):
        week_events = EventHelper.getWeekEvents()

        self.template_values.update({
            "events": week_events,
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/index_competitionseason.html')
        return template.render(path, self.template_values)


class MainInsightsHandler(CacheableHandler):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "main_insights"

    def __init__(self, *args, **kw):
        super(MainInsightsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _render(self, *args, **kw):
        week_events = EventHelper.getWeekEvents()
        year = datetime.datetime.now().year
        self.template_values.update({
            "events": week_events,
            "year": year,
        })

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(year, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        for insight in insights:
            if insight:
                self.template_values[insight.name] = insight

        path = os.path.join(os.path.dirname(__file__), '../templates/index_insights.html')
        return template.render(path, self.template_values)


class MainOffseasonHandler(CacheableHandler):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "main_offseason"

    def __init__(self, *args, **kw):
        super(MainOffseasonHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _render(self, *args, **kw):
        week_events = EventHelper.getWeekEvents()
        self.template_values.update({
            "events": week_events,
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/index_offseason.html')
        return template.render(path, self.template_values)


class ContactHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_contact"

    def __init__(self, *args, **kw):
        super(ContactHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/contact.html")
        return template.render(path, self.template_values)


class HashtagsHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_hashtags"

    def __init__(self, *args, **kw):
        super(HashtagsHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/hashtags.html")
        return template.render(path, self.template_values)


class AboutHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_about"

    def __init__(self, *args, **kw):
        super(AboutHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/about.html")
        return template.render(path, self.template_values)


class ThanksHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_thanks"

    def __init__(self, *args, **kw):
        super(ThanksHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/thanks.html")
        return template.render(path, self.template_values)


class OprHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_opr"

    def __init__(self, *args, **kw):
        super(OprHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/opr.html")
        return template.render(path, self.template_values)


class SearchHandler(webapp2.RequestHandler):
    def get(self):
        try:
            q = self.request.get("q")
            logging.info("search query: %s" % q)
            if q.isdigit():
                team_id = "frc%s" % q
                team = Team.get_by_id(team_id)
                if team:
                    self.redirect(team.details_url)
                    return None
            elif len(q) in {3, 4, 5}:  # event shorts are between 3 and 5 characters long
                year = datetime.datetime.now().year  # default to current year
                event_id = "%s%s" % (year, q)
                event = Event.get_by_id(event_id)
                if event:
                    self.redirect(event.details_url)
                    return None
        except Exception, e:
            logging.warning("warning: %s" % e)
        finally:
            self.response.out.write(render_static("search"))


class GamedayHandler(CacheableHandler):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "main_gameday"

    def __init__(self, *args, **kw):
        super(GamedayHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60

    def _render(self, *args, **kw):
        special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
        special_webcasts_temp = special_webcasts_future.get_result()
        if special_webcasts_temp:
            special_webcasts_temp = special_webcasts_temp.contents
        else:
            special_webcasts_temp = {}
        special_webcasts = []
        for webcast in special_webcasts_temp.values():
            toAppend = {}
            for key, value in webcast.items():
                toAppend[str(key)] = str(value)
            special_webcasts.append(toAppend)

        ongoing_events = []
        ongoing_events_w_webcasts = []
        week_events = EventHelper.getWeekEvents()
        for event in week_events:
            if event.now:
                ongoing_events.append(event)
                if event.webcast:
                    valid = []
                    for webcast in event.webcast:
                        if 'type' in webcast and 'channel' in webcast:
                            event_webcast = {'event': event}
                            valid.append(event_webcast)
                    # Add webcast numbers if more than one for an event
                    if len(valid) > 1:
                        count = 1
                        for event in valid:
                            event['count'] = count
                            count += 1
                    ongoing_events_w_webcasts += valid

        self.template_values.update({
            'special_webcasts': special_webcasts,
            'ongoing_events': ongoing_events,
            'ongoing_events_w_webcasts': ongoing_events_w_webcasts
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/gameday.html')
        return template.render(path, self.template_values)


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

        path = os.path.join(os.path.dirname(__file__), '../templates/webcasts.html')
        return template.render(path, self.template_values)


class RecordHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_record"

    def __init__(self, *args, **kw):
        super(RecordHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/record.html")
        return template.render(path, self.template_values)


class ApiDocumentationHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "api_docs"

    def __init__(self, *args, **kw):
        super(ApiDocumentationHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/apidocs.html")
        return template.render(path, self.template_values)


class ApiWriteHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "api_write"

    def __init__(self, *args, **kw):
        super(ApiWriteHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/apiwrite.html")
        return template.render(path, self.template_values)


class MatchInputHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "match_input"

    def __init__(self, *args, **kw):
        super(MatchInputHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/matchinput.html")
        return template.render(path, self.template_values)


class WebhookDocumentationHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "webhook_docs"

    def __init__(self, *args, **kw):
        super(WebhookDocumentationHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        self.template_values['enabled'] = NotificationType.enabled_notifications
        self.template_values['types'] = NotificationType.types
        path = os.path.join(os.path.dirname(__file__), "../templates/webhookdocs.html")
        return template.render(path, self.template_values)
