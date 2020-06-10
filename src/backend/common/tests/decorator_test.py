from backend.common.decorators import cached_public
from flask import Flask


def test_no_cached_public(app: Flask) -> None:
    @app.route("/")
    def view():
        return "Hello!"

    resp = app.test_client().get("/")
    assert resp.headers.get("Cache-Control") is None


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
