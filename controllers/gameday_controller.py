import datetime
import os
import json

import webapp2
from google.appengine.ext.webapp import template

from controllers.base_controller import CacheableHandler
from database.event_query import TeamYearEventsQuery
from helpers.event_helper import EventHelper
from helpers.model_to_dict import ModelToDict
from helpers.validation_helper import ValidationHelper
from models.event import Event
from models.sitevar import Sitevar

from base_controller import CacheableHandler

from helpers.event_helper import EventHelper


class Gameday2Controller(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_gameday2"

    def __init__(self, *args, **kw):
        super(Gameday2Controller, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
        special_webcasts_temp = special_webcasts_future.get_result()
        if special_webcasts_temp:
            special_webcasts_temp = special_webcasts_temp.contents.get("webcasts", [])
        else:
            special_webcasts_temp = []
        special_webcasts = []
        for webcast in special_webcasts_temp:
            toAppend = {}
            for key, value in webcast.items():
                toAppend[str(key)] = str(value)
            special_webcasts.append(toAppend)

        ongoing_events = []
        ongoing_events_w_webcasts = []
        week_events = EventHelper.getWeekEvents()
        for event in week_events:
            if event.now:
                ongoing_events.append(ModelToDict.eventConverter(event))
                if event.webcast:
                    ongoing_events_w_webcasts.append(ModelToDict.eventConverter(event))

        webcasts_json = {
            'special_webcasts': special_webcasts,
            'ongoing_events': ongoing_events,
            'ongoing_events_w_webcasts': ongoing_events_w_webcasts
        }

        self.template_values.update({
            'webcasts_json': json.dumps(webcasts_json)
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/gameday2.html')
        return template.render(path, self.template_values)


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
            special_webcasts_temp = special_webcasts_temp.contents.get("webcasts", [])
        else:
            special_webcasts_temp = []
        special_webcasts = []
        special_webcast_keys = set()
        for webcast in special_webcasts_temp:
            toAppend = {}
            for key, value in webcast.items():
                toAppend[str(key)] = str(value)
            special_webcasts.append(toAppend)
            special_webcast_keys.add(webcast['key_name'])

        ongoing_events = []
        ongoing_events_w_webcasts = []
        week_events = EventHelper.getWeekEvents()
        for event in week_events:
            if event.now and event.key.id() not in special_webcast_keys:
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


class GamedayRedirectHandler(webapp2.RequestHandler):

    def get(self, alias):
        special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
        special_webcasts = special_webcasts_future.get_result()
        aliases = special_webcasts.contents.get("aliases", {}) if special_webcasts else {}

        if alias in aliases:
            self.redirect("/gameday{}".format(aliases[alias]))
            return

        # Allow an alias to be an event key
        if not ValidationHelper.event_id_validator(alias):
            event = Event.get_by_id(alias)
            if event and event.webcast and event.within_a_day:
                params = self.get_param_string_for_event(event)
                self.redirect("/gameday{}".format(params))
                return

        # Allow an alias to be a team number
        team_key = "frc{}".format(alias)
        if not ValidationHelper.team_id_validator(team_key):
            now = datetime.datetime.now()
            team_events_future = TeamYearEventsQuery(team_key, now.year).fetch_async()
            team_events = team_events_future.get_result()
            for event in team_events:
                if event and event.webcast and event.within_a_day:
                    params = self.get_param_string_for_event(event)
                    self.redirect("/gameday{}".format(params))
                    return

        self.redirect("/gameday")
        return

    @staticmethod
    def get_param_string_for_event(event):
        count = len(event.webcast)
        if count == 0:
            return ""
        layout = count - 1 if count < 5 else 5  # Fall back to hex-view
        params = "#layout={}".format(layout)
        for i, webcast in enumerate(event.webcast):
            params += "&view_{}={}-{}".format(i, webcast['key_name'], i+1)

        return params