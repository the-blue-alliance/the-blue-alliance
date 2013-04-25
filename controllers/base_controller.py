import webapp2
import email.utils
import hashlib
import hmac
import base64
import time
from webapp2_extras import auth, sessions

import cgi
import urllib
from django.utils import simplejson as json

from google.appengine.api import memcache

import tba_config

from models.sitevar import Sitevar

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
        return "{}:{}:{}".format(
            self._cache_key,
            self._cache_version,
            tba_config.CONFIG["static_resource_version"])

    def get(self, *args, **kw):
        content = self._read_cache()
        if not content:
            content = self._render(*args, **kw)
            self._write_cache(content)
        self.response.out.write(content)
        
    def memcacheFlush(self):
        memcache.delete(self.cache_key)
        return self.cache_key

    def _read_cache(self):
        return memcache.get(self.cache_key)

    def _render(self):
        raise NotImplementedError("No _render method.")

    def _write_cache(self, content):
        if tba_config.CONFIG["memcache"]: memcache.set(self.cache_key, content, self._cache_expiration)


class BaseHandler(webapp2.RequestHandler):

    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key"""
        return self.session_store.get_session()

    @webapp2.cached_property
    def auth(self):
            return auth.get_auth()
  
    @webapp2.cached_property
    def current_user(self):
        """Returns currently logged in user"""
        user_dict = self.auth.get_user_by_session()
        return self.auth.store.user_model.get_by_id(user_dict['user_id'])
      
    @webapp2.cached_property
    def logged_in(self):
        """Returns true if a user is currently logged in, false otherwise"""
        return self.auth.get_user_by_session() is not None

    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

