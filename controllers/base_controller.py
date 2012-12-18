import webapp2
from webapp2_extras import sessions

from google.appengine.api import memcache

import facebook
import tba_config

from models.user import User

class CacheableHandler(webapp2.RequestHandler):
    """
    Provides a standard way of caching the output of pages.
    """

    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 0
        self._cache_key = ""
        self._cache_version = 0

    @property
    def cache_key(self):
        return "{}:{}".format(self._cache_key, self._cache_version)

    def get(self, *args, **kw):
        content = self._read_cache()
        if not content:
            content = self._render(*args, **kw)
            self._write_cache(content)
        self.response.out.write(content)

    def _read_cache(self):
        return memcache.get(self.cache_key)

    def _render(self):
        raise NotImplementedError("No _render method.")

    def _write_cache(self, content):
        if tba_config.CONFIG["memcache"]: memcache.set(self.cache_key, content, self._cache_expiration)



class BaseHandler(webapp2.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    @property
    def current_user(self):
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, tba_config.CONFIG['FACEBOOK_APP_ID'], tba_config.CONFIG['FACEBOOK_APP_SECRET'])
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = User.get_by_key_name(cookie["uid"])
                if not user:
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = User(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                profile_url=profile["link"],
                                access_token=cookie["access_token"])
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()
                self._current_user = user
        return self._current_user
