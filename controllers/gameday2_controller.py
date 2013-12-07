import os

from google.appengine.ext.webapp import template

from base_controller import CacheableHandler

class Gameday2Controller(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_gameday2"
        self._cache_version = 1

    def _render(self, *args, **kw):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), '../templates/gameday2.html')
        return template.render(path, template_values)
