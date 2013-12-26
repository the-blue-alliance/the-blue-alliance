import os

from google.appengine.ext.webapp import template

from models.sitevar import Sitevar

from base_controller import CacheableHandler

class Gameday2Controller(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_gameday2"
        self._cache_version = 1

    def _render(self, *args, **kw):
        template_values = {}

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

        template_values = {'special_webcasts': special_webcasts}

        path = os.path.join(os.path.dirname(__file__), '../templates/gameday2.html')
        return template.render(path, template_values)
