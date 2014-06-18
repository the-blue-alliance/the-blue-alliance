import os

from google.appengine.ext.webapp import template

from base_controller import CacheableHandler
from models.event import Event
from models.match import Match


class MatchDetail(CacheableHandler):
    """
    Display a Match.
    """
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "match_detail_{}"  # (match_key)

    def __init__(self, *args, **kw):
        super(MatchDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, match_key):
        if not match_key:
            return self.redirect("/")

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(match_key)
        super(MatchDetail, self).get(match_key)

    def _render(self, match_key):
        try:
            match_future = Match.get_by_id_async(match_key)
            event_future = Event.get_by_id_async(match_key.split("_")[0])
            match = match_future.get_result()
            event = event_future.get_result()
        except Exception, e:
            self.abort(404)

        if not match:
            self.abort(404)

        template_values = {
            "event": event,
            "match": match,
        }

        if event.within_a_day:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        path = os.path.join(os.path.dirname(__file__), '../templates/match_details.html')
        return template.render(path, template_values)
