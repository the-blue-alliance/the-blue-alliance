import datetime
import time
from datetime import timedelta

from flask import Flask, make_response, Response
from flask_caching import CachedResponse
from freezegun import freeze_time
from werkzeug.http import http_date

from backend.common.cache.flask_response_cache import MemcacheFlaskResponseCache
from backend.common.decorators import cached_public, memoize
from backend.common.flask_cache import configure_flask_cache, make_cached_response
from backend.common.sitevars.turbo_mode import ContentType as TurboCfg, TurboMode


def test_no_cached_public(app: Flask) -> None:
    @app.route("/")
    def view():
        return "Hello!"

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") is None
    assert resp.headers.get("ETag") is None


def test_no_cached_public_on_error(app: Flask) -> None:
    @app.route("/")
    @cached_public
    def view():
        return "Error", 401

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") is None
    assert resp.headers.get("ETag") is None


def test_cached_public_default(app: Flask) -> None:
    @app.route("/")
    @cached_public
    def view():
        return "Hello!"

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") == "public, max-age=61, s-maxage=61"


def test_cached_public_timeout(app: Flask) -> None:
    @app.route("/")
    @cached_public(ttl=3600)
    def view():
        return "Hello!"

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") == "public, max-age=3600, s-maxage=3600"


def test_cached_public_timedelta(app: Flask) -> None:
    # Test that decimal timedeltas resolve to integers
    @app.route("/")
    @cached_public(ttl=timedelta(hours=1, seconds=1.5))
    def view():
        return "Hello!"

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") == "public, max-age=3601, s-maxage=3601"


def test_cached_public_timeout_dynamic(app: Flask) -> None:
    @app.route("/")
    @cached_public(ttl=3600)
    def view():
        # This should take precedence over the static timeout
        return CachedResponse(make_response("Hello!"), 600)

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") == "public, max-age=600, s-maxage=600"


@freeze_time("2020-01-01")
def test_cached_public_turbo_mode(app: Flask) -> None:
    @app.route("/turbo")
    @cached_public(ttl=3600)
    def view() -> Response:
        return make_cached_response(make_response("Hello!"), ttl=timedelta(minutes=10))

    TurboMode.put(
        TurboCfg(
            regex=r".*turbo.*",
            valid_until=datetime.datetime(2020, 1, 2).timestamp(),
            cache_length=61,
        )
    )
    resp = app.test_client().get("/turbo")
    assert resp.headers.get("Cache-Control") == "public, max-age=61, s-maxage=61"


@freeze_time("2020-01-03")
def test_cached_public_turbo_mode_expired(app: Flask) -> None:
    @app.route("/turbo")
    @cached_public(ttl=3600)
    def view() -> Response:
        return make_cached_response(make_response("Hello!"), ttl=timedelta(minutes=10))

    TurboMode.put(
        TurboCfg(
            regex=r".*turbo.*",
            valid_until=datetime.datetime(2020, 1, 2).timestamp(),
            cache_length=61,
        )
    )
    resp = app.test_client().get("/turbo")
    assert resp.headers.get("Cache-Control") == "public, max-age=600, s-maxage=600"


def test_cached_public_etag(app: Flask) -> None:
    @app.route("/")
    @cached_public
    def view():
        return "Hello!"

    resp = app.test_client().get("/")
    etag = resp.headers.get("ETag")
    assert etag is not None

    # Check that a valid etag returns 304
    resp2 = app.test_client().get("/", headers={"If-None-Match": etag})
    assert resp2.status_code == 304
    assert resp2.get_data(as_text=True) == ""

    # Check that an invalid etag returns a normal response
    resp3 = app.test_client().get("/", headers={"If-None-Match": "bad-etag"})
    assert resp3.status_code == 200
    assert resp3.get_data(as_text=True) == "Hello!"


def test_cached_304_not_modified(app: Flask) -> None:
    start_time = datetime.datetime.now()

    @app.route("/")
    @cached_public
    def view():
        response = make_response("Hello!")
        response.last_modified = start_time
        return response

    resp = app.test_client().get("/")
    last_modified = resp.headers.get("Last-Modified")
    assert last_modified is not None
    assert last_modified == http_date(start_time)

    # If we're asking for the same data as we've last received
    resp2 = app.test_client().get(
        "/", headers={"If-Modified-Since": http_date(start_time)}
    )
    assert resp2.status_code == 304
    assert resp2.get_data(as_text=True) == ""

    # Check that if we ask for a newer time, we'll get the data back
    resp3 = app.test_client().get(
        "/",
        headers={
            "If-Modified-Since": http_date(start_time + datetime.timedelta(seconds=-1))
        },
    )
    assert resp3.status_code == 200
    assert resp3.get_data(as_text=True) == "Hello!"

    # But if we ask for something newer, we get the response back
    resp3 = app.test_client().get(
        "/",
        headers={
            "If-Modified-Since": http_date(start_time + datetime.timedelta(seconds=1))
        },
    )
    assert resp3.status_code == 304
    assert resp3.get_data(as_text=True) == ""


def test_flask_cache_with_memcache(app: Flask, memcache_stub) -> None:
    configure_flask_cache(app)

    @app.route("/")
    @cached_public
    def view():
        return "Hello!"

    assert hasattr(app, "cache")
    assert isinstance(app.cache.cache, MemcacheFlaskResponseCache)  # pyre-ignore[16]

    resp = app.test_client().get("/")
    assert resp.status_code == 200

    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") == resp.data.decode()


def test_flask_cache_with_memcache_static_timeout(app: Flask, memcache_stub) -> None:
    configure_flask_cache(app)

    @app.route("/")
    @cached_public(ttl=1)
    def view():
        return "Hello!"

    assert hasattr(app, "cache")
    assert isinstance(app.cache.cache, MemcacheFlaskResponseCache)  # pyre-ignore[16]

    resp = app.test_client().get("/")
    assert resp.status_code == 200

    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") == resp.data.decode()
    time.sleep(1)
    # cache is expired by now
    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") is None


def test_flask_cache_with_memcache_dynamic_timeout(app: Flask, memcache_stub) -> None:
    configure_flask_cache(app)

    @app.route("/")
    @cached_public(ttl=1)
    def view():
        return CachedResponse(make_response("Hello!"), 2)

    assert hasattr(app, "cache")
    assert isinstance(app.cache.cache, MemcacheFlaskResponseCache)  # pyre-ignore[16]

    resp = app.test_client().get("/")
    assert resp.status_code == 200

    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") is not None

    # cache shouldn't be expired yet
    time.sleep(1)
    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") is not None

    # but now it should
    time.sleep(1)
    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") is None


def test_flask_cache_with_query_string(app: Flask, memcache_stub) -> None:
    configure_flask_cache(app)

    @app.route("/")
    @cached_public
    def view():
        return "Hello!"

    assert hasattr(app, "cache")
    assert isinstance(app.cache.cache, MemcacheFlaskResponseCache)  # pyre-ignore[16]

    resp = app.test_client().get("/")
    assert resp.status_code == 200

    # Make sure the query string version has a different cache key
    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") is not None
    assert app.cache.get("/556df1cd959b2932289548d8810cc66e") is None

    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") == resp.data.decode()

    resp_query = app.test_client().get("/?query_string=TBA")
    assert resp_query.status_code == 200

    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") is not None
    assert app.cache.get("/556df1cd959b2932289548d8810cc66e") is not None

    assert app.cache.get("/bcd8b0c2eb1fce714eab6cef0d771acc") == resp.data.decode()
    assert (
        app.cache.get("/556df1cd959b2932289548d8810cc66e") == resp_query.data.decode()
    )


def test_flask_cache_with_memcache_skips_errors(app: Flask, memcache_stub) -> None:
    configure_flask_cache(app)

    @app.route("/")
    @cached_public
    def view():
        return "Hello!", 500

    assert hasattr(app, "cache")
    assert isinstance(app.cache.cache, MemcacheFlaskResponseCache)  # pyre-ignore[16]

    resp = app.test_client().get("/")
    assert resp.status_code == 500
    assert app.cache.get("view//") is None


def test_memoize_outside_of_request(app: Flask) -> None:
    @memoize
    def an_expensive_function():
        an_expensive_function.counter += 1
        return an_expensive_function.counter

    an_expensive_function.counter = 0

    resp1 = an_expensive_function()
    assert resp1 == 1

    # By deafult, we shouldn't have memoized anything (because redis isn't configured)
    resp2 = an_expensive_function()
    assert resp2 == 2


def test_memoize_without_setup(app: Flask) -> None:
    @memoize
    def an_expensive_function():
        an_expensive_function.counter += 1
        return an_expensive_function.counter

    an_expensive_function.counter = 0

    @app.route("/")
    def view():
        return str(an_expensive_function())

    resp1 = app.test_client().get("/")
    assert resp1.status_code == 200
    assert resp1.data == b"1"

    # By deafult, we shouldn't have memoized anything (because redis isn't configured)
    resp2 = app.test_client().get("/")
    assert resp2.status_code == 200
    assert resp2.data == b"2"


def test_memoize_with_memcache(app: Flask, memcache_stub) -> None:
    configure_flask_cache(app)

    @memoize
    def an_expensive_function():
        an_expensive_function.counter += 1
        return an_expensive_function.counter

    an_expensive_function.counter = 0

    @app.route("/")
    def view():
        return str(an_expensive_function())

    resp1 = app.test_client().get("/")
    assert resp1.status_code == 200
    assert resp1.data == b"1"

    # The second time we call the function, we should have cached the result
    resp2 = app.test_client().get("/")
    assert resp2.status_code == 200
    assert resp2.data == b"1"
