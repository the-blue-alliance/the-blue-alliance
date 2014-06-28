import logging
import webapp2

from time import mktime
from wsgiref.handlers import format_date_time

from google.appengine.api import memcache

import tba_config

from helpers.user_bundle import UserBundle


class CacheableHandler(webapp2.RequestHandler):
    """
    Provides a standard way of caching the output of pages.
    Currently only supports logged-out pages.
    """
    CACHE_KEY_FORMAT = ''

    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 0
        if not hasattr(self, '_partial_cache_key'):
            self._partial_cache_key = self.CACHE_KEY_FORMAT

        # Cache all pages for 61 seconds, unless overwritten.
        if self.response is not None:
            self.response.headers['Cache-Control'] = 'public, max-age=61'
            self.response.headers['Pragma'] = 'Public'

        self.template_values = {}

    @property
    def cache_key(self):
        return self._render_cache_key(self._partial_cache_key)

    @classmethod
    def get_cache_key_from_format(cls, *args):
        return cls._render_cache_key(cls.CACHE_KEY_FORMAT.format(*args))

    @classmethod
    def _render_cache_key(cls, cache_key):
        return "{}:{}:{}".format(
            cache_key,
            cls.CACHE_VERSION,
            tba_config.CONFIG["static_resource_version"])

    def get(self, *args, **kw):
        cached_response = self._read_cache()
        if cached_response is True:
            pass
        elif cached_response is not None:
            self.response.out.write(cached_response.body)
            self.response.headers = cached_response.headers
        else:
            self.template_values["cache_key"] = self.cache_key
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
        memcache.delete(self.cache_key)
        return self.cache_key

    def _read_cache(self):
        return memcache.get(self.cache_key)

    def _write_cache(self, response):
        if tba_config.CONFIG["memcache"]:
            memcache.set(self.cache_key, response, self._cache_expiration)

    @classmethod
    def delete_cache_multi(cls, cache_keys):
        memcache.delete_multi(cache_keys)

    def _render(self):
        raise NotImplementedError("No _render method.")


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
