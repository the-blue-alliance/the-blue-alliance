from flask import Flask

from backend.common.decorators import cached_public


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
    @cached_public(timeout=3600)
    def view():
        return "Hello!"

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") == "public, max-age=3600, s-maxage=3600"


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
