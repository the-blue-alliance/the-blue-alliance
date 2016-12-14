import os

from google.appengine.ext.webapp import template
from base_controller import CacheableHandler


# Note, broken out into its own class for future extensibility -PJL 04272015
class EventWizardHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "event_wizard"

    def __init__(self, *args, **kw):
        super(EventWizardHandler, self).__init__(*args, **kw)
        self.cache_expiration = 60 * 60

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/eventwizard.html")

        return template.render(path, self.template_values)
