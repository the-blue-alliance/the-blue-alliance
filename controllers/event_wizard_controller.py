import os

from google.appengine.ext.webapp import template
from base_controller import CacheableHandler


class EventWizardHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "event_wizard"

    def __init__(self, *args, **kw):
        super(EventWizardHandler, self).__init__(*args, **kw)
        self.cache_expiration = 60 * 60

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/eventwizard.html")

        return template.render(path, self.template_values)


class ReactEventWizardHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "event_wizard_react"

    def __init__(self, *args, **kw):
        super(ReactEventWizardHandler, self).__init__(*args, **kw)
        self.cache_expiration = 60 * 60

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/react-eventwizard.html")

        return template.render(path, self.template_values)
