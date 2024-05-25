import os

from google.appengine.ext.webapp import template

from consts.notification_type import NotificationType
from controllers.base_controller import CacheableHandler
from template_engine import jinja2_engine


class AddDataHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "add_data_instructions"

    def __init__(self, *args, **kw):
        super(AddDataHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('add_data.html', self.template_values)
