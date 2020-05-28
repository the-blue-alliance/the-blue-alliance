import cPickle
import datetime
import hashlib
import time
import logging
import re
import webapp2
import zlib

from time import mktime
from wsgiref.handlers import format_date_time

from google.appengine.api import memcache

import tba_config

from helpers.user_bundle import UserBundle
from models.sitevar import Sitevar
from models.team_admin_access import TeamAdminAccess
from stackdriver.profiler import trace_context, TraceContext


class CacheableHandler(webapp2.RequestHandler):
    """
    Provides a standard way of caching the output of pages.
    Currently only supports logged-out pages.
    """
    CACHE_KEY_FORMAT = ''
    CACHE_HEADER_LENGTH = 61
    SHOULD_ADD_ADMIN_BAR = True

    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        if type(self.request) == webapp2.Request:
            trace_context.request = self.request

        with TraceContext(sendTrace=False) as root:
            with root.span("CacheableHandler.__init__"):
                self._cache_expiration = 0
                self._last_modified = None  # A datetime object
                self._user_bundle = UserBundle()
                self._is_admin = self._user_bundle.is_current_user_admin
                if not hasattr(self, '_partial_cache_key'):
                    self._partial_cache_key = self.CACHE_KEY_FORMAT
                self.template_values = {}
                if self.response:
                    self.response.headers['Vary'] = 'Accept-Encoding'

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

    def _add_admin_bar(self, html):
        if self._is_admin and self.SHOULD_ADD_ADMIN_BAR:
            from template_engine import jinja2_engine
            self.template_values["cache_key"] = self.cache_key
            self.template_values["return_url"] = self.request.path
            self.template_values["flushed"] = self.request.get("flushed")
            self.template_values["user_bundle"] = self._user_bundle
            admin_bar = jinja2_engine.render('admin_bar.html', self.template_values)
            return html.replace('<!-- Admin Bar -->', admin_bar.encode('utf8'))
        else:
            return html

    def get(self, *args, **kw):
        with TraceContext() as root:
            with root.span("CacheableHandler.get"):
                with root.span("CacheableHandler._read_cache"):
                    cached_response = self._read_cache()

                if cached_response is None:
                    self._set_cache_header_length(self.CACHE_HEADER_LENGTH)
                    self.template_values["render_time"] = datetime.datetime.now().replace(second=0, microsecond=0)  # Prevent ETag from changing too quickly
                    with root.span("CacheableHandler._render"):
                        rendered = self._render(*args, **kw)
                    if self._output_if_modified(self._add_admin_bar(rendered)):
                        self._write_cache(self.response)
                else:
                    self.response.headers.update(cached_response.headers)
                    del self.response.headers['Content-Length']  # Content-Length gets set automatically
                    self._output_if_modified(self._add_admin_bar(cached_response.body))

    def _output_if_modified(self, content):
        """
        Check for ETag, then fall back to If-Modified-Since
        """
        with TraceContext() as root:
            with root.span("CacheableHandler._output_if_modified"):
                modified = True

                # Normalize content
                try:
                    content = str(content)
                except UnicodeEncodeError:
                    content = unicode(content).encode('utf-8')

                etag = 'W/"{}"'.format(hashlib.md5(content).hexdigest())  # Weak ETag
                self.response.headers['ETag'] = etag

                if_none_match = self.request.headers.get('If-None-Match')
                if if_none_match and etag in [x.strip() for x in if_none_match.split(',')]:
                    self.response.set_status(304)
                    modified = False

                # Fall back to If-Modified-Since
                if modified and self._last_modified is not None:
                    last_modified = format_date_time(mktime(self._last_modified.timetuple()))
                    if_modified_since = self.request.headers.get('If-Modified-Since')
                    self.response.headers['Last-Modified'] = last_modified
                    if if_modified_since and if_modified_since == last_modified:
                        self.response.set_status(304)
                        modified = False

                if modified:
                    self.response.out.write(content)

                return modified

    def memcacheFlush(self):
        memcache.delete(self.cache_key)
        return self.cache_key

    def _read_cache(self):
        compressed_result = memcache.get(self.cache_key)
        if compressed_result is None:
            return None
        else:
            response, last_modified = cPickle.loads(zlib.decompress(compressed_result))
            self._last_modified = last_modified
            return response

    def _write_cache(self, response):
        if tba_config.CONFIG["memcache"] and not self._is_admin:
            compressed = zlib.compress(cPickle.dumps((response, self._last_modified)))
            try:
                memcache.set(self.cache_key, compressed, self._get_cache_expiration())
            except ValueError:
                logging.info("Setting memcache failed for key: {}".format(self.cache_key))

    @classmethod
    def delete_cache_multi(cls, cache_keys):
        memcache.delete_multi(cache_keys)

    def _get_cache_expiration(self):
        turbo_sitevar = Sitevar.get_by_id('turbo_mode')
        if not turbo_sitevar or not turbo_sitevar.contents:
            return self._cache_expiration
        contents = turbo_sitevar.contents
        regex = contents['regex'] if 'regex' in contents else "$^"
        pattern = re.compile(regex)
        valid_until = contents.get('valid_until', -1)  # UNIX time
        cache_length = contents.get('cache_length', self._cache_expiration)
        now = time.time()

        if now <= int(valid_until) and pattern.match(self.cache_key):
            return cache_length
        else:
            return self._cache_expiration

    def _render(self):
        raise NotImplementedError("No _render method.")

    def _set_cache_header_length(self, seconds):
        if type(seconds) is not int:
            logging.error("Cache-Control max-age is not integer: {}".format(seconds))
            return

        if not self._is_admin:
            seconds = min(seconds, self._get_cache_expiration)  # Cache header should never be longer than memcache
            self.response.headers['Cache-Control'] = "public, max-age={0}, s-maxage={0}".format(max(int(seconds), 61))  # needs to be at least 61 seconds to work


class LoggedInHandler(webapp2.RequestHandler):
    """
    Provides a base set of functionality for pages that need logins.
    Currently does not support caching as easily as CacheableHandler.
    """

    def __init__(self, *args, **kw):
        super(LoggedInHandler, self).__init__(*args, **kw)
        if type(self.request) == webapp2.Request:
            trace_context.request = self.request

        self.user_bundle = UserBundle()
        self.template_values = {
            "user_bundle": self.user_bundle
        }
        self.response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        self.response.headers['Pragma'] = 'no-cache'
        self.response.headers['Expires'] = '0'
        self.response.headers['Vary'] = 'Accept-Encoding'
        self.response.headers['X-Robots-Tag'] = 'noindex'

    def _get_login_url(self, target_url):
        return self.user_bundle.create_login_url(target_url)

    def _require_admin(self):
        self._require_login()
        if not self.user_bundle.is_current_user_admin:
            return self.redirect(self.user_bundle.login_url, abort=True)

    def _require_login(self, redirect_url=None):
        import urllib

        if not self.user_bundle.user:
            if not redirect_url:
                redirect_url = self.request.get('redirect')
            if not redirect_url:
                redirect_url = self.request.url
            return self.redirect(
                '/account/login_required?redirect={}'.format(urllib.quote(redirect_url)),
                abort=True
            )

    def _require_permission(self, permission):
        self._require_registration()
        if permission not in self.user_bundle.account.permissions:
            return self.redirect(
                "/",
                abort=True
            )

    def _require_registration(self, redirect_url=None):
        import urllib

        self._require_login()
        if not self.user_bundle.account.registered:
            if not redirect_url:
                redirect_url = self.request.get('redirect')
            if not redirect_url:
                redirect_url = self.request.url
            return self.redirect(
                '/account/register?redirect={}'.format(urllib.quote(redirect_url)),
                abort=True
            )

    def _require_team_admin_access(self, team_number, redirect_url=None):
        self._require_login(redirect_url)
        if self.user_bundle.is_current_user_admin:
            # Admins have this granted
            return

        user = self.user_bundle.account.key
        now = datetime.datetime.now()
        existing_access = existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == user,
            TeamAdminAccess.team_number == team_number,
            TeamAdminAccess.expiration > now).fetch()
        if not existing_access:
            return self.abort(403)

    def _require_request_user_is_bundle_user(self):
        current_user_account_id = self.user_bundle.account.key.id()

        target_account_id = self.request.get('account_id')
        if not target_account_id:
            return self.abort(403)

        if target_account_id != current_user_account_id:
            return self.abort(403)
