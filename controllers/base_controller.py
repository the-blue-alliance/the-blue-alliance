import json
import logging
import webapp2

from time import mktime
from wsgiref.handlers import format_date_time

from google.appengine.api import memcache
from google.appengine.ext import ndb

import tba_config

from helpers.user_bundle import UserBundle
from models.cached_response import CachedResponse


class CacheableHandler(webapp2.RequestHandler):
    """
    Provides a standard way of caching the output of pages.
    Currently only supports logged-out pages.
    """
    CACHE_KEY_FORMAT = ''

    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 0
        if not hasattr(self, '_cache_key'):
            self._cache_key = self.CACHE_KEY_FORMAT

        # Cache all pages for 61 seconds, unless overwritten.
        if self.response is not None:
            self.response.headers['Cache-Control'] = 'public, max-age=61'
            self.response.headers['Pragma'] = 'Public'

    @property
    def full_cache_key(self):
        return self._get_full_cache_key(self._cache_key)

    @classmethod
    def _get_full_cache_key(cls, cache_key):
        return "{}:{}:{}".format(
            cache_key,
            cls.CACHE_VERSION,
            tba_config.CONFIG["static_resource_version"])

    def get(self, *args, **kw):
        cached_response = memcache.get(self.full_cache_key)
        if cached_response:
            self.response.out.write(cached_response.body)
            self.response.headers = cached_response.headers
        else:
            ndb_cached_response = CachedResponse.get_by_id(self.full_cache_key)
            if ndb_cached_response:
                self.response.out.write(ndb_cached_response.body)
                for key, value in ndb_cached_response.headers.items():
                    self.response.headers[str(key)] = str(value)
            else:
                self.response.out.write(self._render(*args, **kw))
            self._write_cache(self.response)

    def _has_been_modified_since(self, datetime):
        last_modified = format_date_time(mktime(datetime.timetuple()))
        if_modified_since = self.request.headers.get('If-Modified-Since')
        if if_modified_since and if_modified_since == last_modified:
            self.response.set_status(304)
            return False
        else:
            self.response.headers['Last-Modified'] = last_modified
            return True

    def memcacheFlush(self):
        memcache.delete(self.full_cache_key)
        return self.full_cache_key

    @classmethod
    def clear_cache(cls, *args):
        full_cache_key = cls._get_full_cache_key(cls.CACHE_KEY_FORMAT.format(*args))
        memcache.delete(full_cache_key)
        ndb.Key(CachedResponse, full_cache_key).delete()
        logging.info("Deleting cache key: {}".format(full_cache_key))

    def _render(self):
        raise NotImplementedError("No _render method.")

    def _write_cache(self, response):
        if tba_config.CONFIG["memcache"]:
            memcache.set(self.full_cache_key, response, self._cache_expiration)
        if tba_config.CONFIG["response_cache"]:
            if str(self.__class__.__module__) in {'controllers.api.api_team_controller', 'controllers.api.api_event_controller'}:  # TODO: enable for all
                CachedResponse(
                    id=self.full_cache_key,
                    headers_json=json.dumps(dict(response.headers)),
                    body=response.body,
                ).put()


class LoggedInHandler(webapp2.RequestHandler):
    """
    Provides a base set of functionality for pages that need logins.
    Currently does not support caching as easily as CacheableHandler.
    """

    def __init__(self, *args, **kw):
        super(LoggedInHandler, self).__init__(*args, **kw)
        self.user_bundle = UserBundle()
        self.template_values = {
            "user_bundle": self.user_bundle
        }

    def _require_admin(self):
        self._require_login()
        if not self.user_bundle.is_current_user_admin:
            return self.redirect(self.user_bundle.login_url, abort=True)

    def _require_login(self, target_url="/"):
        if not self.user_bundle.user:
            return self.redirect(
                self.user_bundle.create_login_url(target_url),
                abort=True
            )
