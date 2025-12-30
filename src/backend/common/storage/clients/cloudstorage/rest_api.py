#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Base and helper classes for Google RESTful APIs."""

# pylint: disable=g-bad-name
# pylint: disable=g-import-not-at-top

# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

__author__ = "guido@google.com (Guido van Rossum)"

__all__ = ["add_sync_methods"]

import logging
import os
import random
import time
from concurrent import futures

import six
from google.appengine.api import app_identity
from google.appengine.api import lib_config
from google.appengine.ext import ndb

from backend.common.storage.clients.cloudstorage import api_utils, common

# pylint: disable=protected-access


@ndb.tasklet
# pylint: disable=g-doc-return-or-yield
def _make_token_async(scopes, token_params=None):
    """Get a fresh authentication token.

    Args:
      scopes: A list of scopes.
      token_params: A dict of parameters that can be used by custom token makers.
        This default token maker does not need any extra information, so this is
        unused.

    Raises:
      An ndb.Return with a tuple (token, expiration_time) where expiration_time is
      seconds since the epoch.
    """

    if common.local_run():
        raise ndb.Return(("stub-token", time.time() + 3600))

    def access_token_as_ndb_future():
        ndb_future = ndb.Future()
        ndb_future.set_result(app_identity.get_access_token(scopes))
        return ndb_future

    del token_params  # unused
    with futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(access_token_as_ndb_future)

    token, expires_at = yield future.result()
    raise ndb.Return((token, expires_at))


class _ConfigDefaults(object):
    # Method to use for creating access tokens to GCS.
    TOKEN_MAKER = _make_token_async


_config = lib_config.register("cloudstorage", _ConfigDefaults.__dict__)


def _make_sync_method(name):
    """Helper to synthesize a synchronous method from an async method name.

    Used by the @add_sync_methods class decorator below.

    Args:
      name: The name of the synchronous method.

    Returns:
      A method (with first argument 'self') that retrieves and calls
      self.<name>, passing its own arguments, expects it to return a
      Future, and then waits for and returns that Future's result.
    """

    def sync_wrapper(self, *args, **kwds):
        method = getattr(self, name)
        future = method(*args, **kwds)
        return future.get_result()

    return sync_wrapper


def add_sync_methods(cls):
    """Class decorator to add synchronous methods corresponding to async methods.

    This modifies the class in place, adding additional methods to it.
    If a synchronous method of a given name already exists it is not
    replaced.

    Args:
      cls: A class.

    Returns:
      The same class, modified in place.
    """
    # Don't use iterkeys() -- cls.__dict__ is modified in the loop!
    for name in list(cls.__dict__.keys()):
        if name.endswith("_async"):
            sync_name = name[:-6]
            if not hasattr(cls, sync_name):
                setattr(cls, sync_name, _make_sync_method(name))
    return cls


class _AE_TokenStorage_(ndb.Model):
    """Entity to store app_identity tokens in memcache."""

    token = ndb.StringProperty(indexed=False)
    expires = ndb.FloatProperty()


# @add_sync_methods. Explicit invocation below replaced this for python25.
class _RestApi(object):
    """Base class for REST-based API wrapper classes.

    This class manages authentication tokens and request retries.  All
    APIs are available as synchronous and async methods; synchronous
    methods are synthesized from async ones by the add_sync_methods()
    function in this module.

    WARNING: Do NOT directly use this api. It's an implementation detail
    and is subject to change at any release.
    """

    def __init__(self, scopes, token_maker=None, retry_params=None, token_params=None):
        """Constructor.

        Args:
          scopes: A scope or a list of scopes.
          token_maker: An asynchronous function of the form
            (scopes, token_params) -> (token, expires).
          retry_params: An instance of api_utils.RetryParams. If None, the
            default for current thread will be used.
          token_params: A dict of parameters that can be used with a custom token
            maker. When no custom token maker is configured, this is unused.
        """

        if isinstance(scopes, six.string_types):
            scopes = [scopes]
        self.scopes = scopes
        self.make_token_async = token_maker or _config.TOKEN_MAKER
        if not retry_params:
            retry_params = api_utils._get_default_retry_params()
        self.retry_params = retry_params
        self.token_params = token_params
        self.user_agent = {"User-Agent": retry_params._user_agent}
        # Generate a random token expiration headroom value in seconds.
        self.expiration_headroom = random.randint(60, 240)

    def __getstate__(self):
        """Store state as part of serialization/pickling."""
        return {
            "scopes": self.scopes,
            "a_maker": (
                None
                if self.make_token_async
                == _make_token_async  # pylint: disable=comparison-with-callable
                else self.make_token_async
            ),
            "retry_params": self.retry_params,
            "token_params": self.token_params,
            "expiration_headroom": self.expiration_headroom,
        }

    def __setstate__(self, state):
        """Restore state as part of deserialization/unpickling."""
        self.__init__(
            state["scopes"],
            token_maker=state["a_maker"],
            retry_params=state["retry_params"],
            token_params=state["token_params"],
        )
        self.expiration_headroom = state["expiration_headroom"]

    @ndb.tasklet
    def do_request_async(
        self,
        url,
        method="GET",
        headers=None,
        payload=None,
        deadline=None,
        callback=None,
    ):
        """Issue one HTTP request.

        It performs async retries using tasklets.

        Args:
          url: the url to fetch.
          method: the method in which to fetch.
          headers: the http headers.
          payload: the data to submit in the fetch.
          deadline: the deadline in which to make the call.
          callback: the call to make once completed.

        Yields:
          The async fetch of the url.
        """
        retry_wrapper = api_utils._RetryWrapper(
            self.retry_params,
            retriable_exceptions=api_utils._RETRIABLE_EXCEPTIONS,
            should_retry=api_utils._should_retry,
        )
        resp = yield retry_wrapper.run(
            self.urlfetch_async,
            url=url,
            method=method,
            headers=headers,
            payload=payload,
            deadline=deadline,
            callback=callback,
            follow_redirects=False,
        )
        raise ndb.Return((resp.status_code, resp.headers, resp.content))

    @ndb.tasklet
    def get_token_async(self, refresh=False):
        """Get an authentication token.

        The token is cached in memcache, keyed by the scopes argument.
        Uses a random token expiration headroom value generated in the constructor
        to eliminate a burst of GET_ACCESS_TOKEN API requests.

        Args:
          refresh: If True, ignore a cached token; default False.

        Yields:
          An authentication token. This token is guaranteed to be non-expired.
        """
        if self.token_params is not None:
            # Unfortunately if there is more than one item in token_params, the cache
            # may have misses/duplicates, but storing it this way allows us to make
            # sure that the key does not incorrectly match multiple token_params
            key = "%s,%s" % (str(self.token_params), ",".join(self.scopes))
        else:
            key = "%s" % ",".join(self.scopes)
        ts = yield _AE_TokenStorage_.get_by_id_async(
            key,
            use_cache=True,
            use_memcache=self.retry_params.memcache_access_token,
            use_datastore=self.retry_params.save_access_token,
        )
        if (
            refresh
            or ts is None
            or ts.expires < (time.time() + self.expiration_headroom)
        ):
            token, expires_at = yield self.make_token_async(
                self.scopes, self.token_params
            )
            timeout = int(expires_at - time.time())
            ts = _AE_TokenStorage_(id=key, token=token, expires=expires_at)
            if timeout > 0:
                yield ts.put_async(
                    memcache_timeout=timeout,
                    use_datastore=self.retry_params.save_access_token,
                    force_writes=True,
                    use_cache=True,
                    use_memcache=self.retry_params.memcache_access_token,
                )
        raise ndb.Return(ts.token)

    @ndb.tasklet
    def urlfetch_async(
        self,
        url,
        method="GET",
        headers=None,
        payload=None,
        deadline=None,
        callback=None,
        follow_redirects=False,
    ):
        """Make an async urlfetch() call.

        This is an async wrapper around urlfetch(). It adds an authentication
        header.

        Args:
          url: the url to fetch.
          method: the method in which to fetch.
          headers: the http headers.
          payload: the data to submit in the fetch.
          deadline: the deadline in which to make the call.
          callback: the call to make once completed.
          follow_redirects: whether or not to follow redirects.

        Yields:
          This returns a Future despite not being decorated with @ndb.tasklet!
        """
        # Initialize access token.
        headers = {} if headers is None else dict(headers)
        # Include the user agent in the header.
        headers.update(self.user_agent)
        try:
            self.token = yield self.get_token_async()
        except app_identity.InternalError as e:
            if os.environ.get("DATACENTER", "").endswith("sandman"):
                self.token = None
                logging.warning(
                    "Could not fetch an authentication token in sandman "
                    "based Appengine devel setup; proceeding without one."
                )
            else:
                raise e
        if self.token:
            headers["authorization"] = "OAuth " + self.token

        deadline = deadline or self.retry_params.urlfetch_timeout

        ctx = ndb.get_context()
        # TODO(guido): Explicitly set validate_certificate to True or False?
        resp = yield ctx.urlfetch(
            url,
            payload=payload,
            method=method,
            headers=headers,
            follow_redirects=follow_redirects,
            deadline=deadline,
            callback=callback,
        )
        raise ndb.Return(resp)


# Explicitly invoke class decorator for use in Python25.
_RestApi = add_sync_methods(_RestApi)
