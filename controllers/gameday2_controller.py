import os
import json

from google.appengine.ext.webapp import template

from helpers.event_helper import EventHelper
from helpers.model_to_dict import ModelToDict
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
            special_webcasts_temp = special_webcasts_temp.contents
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
