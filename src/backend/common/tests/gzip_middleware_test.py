import gzip
import json

from flask import Flask, jsonify, Response

from backend.common.gzip_middleware import configure_gzip

LARGE_BODY = {"data": "x" * 2000}
GZIP_HEADERS = {"Accept-Encoding": "gzip"}


def test_gzip_applied_when_accepted(app: Flask) -> None:
    configure_gzip(app)

    @app.route("/")
    def view():
        return jsonify(LARGE_BODY)

    resp = app.test_client().get("/", headers=GZIP_HEADERS)
    assert resp.headers.get("Content-Encoding") == "gzip"
    assert json.loads(gzip.decompress(resp.data)) == LARGE_BODY


def test_identity_without_accept_encoding(app: Flask) -> None:
    configure_gzip(app)

    @app.route("/")
    def view():
        return jsonify(LARGE_BODY)

    resp = app.test_client().get("/")
    assert resp.headers.get("Content-Encoding") is None
    assert json.loads(resp.data) == LARGE_BODY


def test_identity_when_gzip_refused(app: Flask) -> None:
    configure_gzip(app)

    @app.route("/")
    def view():
        return jsonify(LARGE_BODY)

    resp = app.test_client().get("/", headers={"Accept-Encoding": "gzip;q=0"})
    assert resp.headers.get("Content-Encoding") is None


def test_small_response_skipped(app: Flask) -> None:
    configure_gzip(app)

    @app.route("/")
    def view():
        return jsonify({"ok": True})

    resp = app.test_client().get("/", headers=GZIP_HEADERS)
    assert resp.headers.get("Content-Encoding") is None


def test_non_compressible_mimetype_skipped(app: Flask) -> None:
    configure_gzip(app)

    @app.route("/")
    def view():
        return Response(b"\x89PNG" + b"\x00" * 2000, mimetype="image/png")

    resp = app.test_client().get("/", headers=GZIP_HEADERS)
    assert resp.headers.get("Content-Encoding") is None


def test_vary_and_weakened_etag(app: Flask) -> None:
    configure_gzip(app)

    @app.route("/")
    def view():
        resp = jsonify(LARGE_BODY)
        resp.add_etag()
        return resp

    resp = app.test_client().get("/", headers=GZIP_HEADERS)
    assert resp.headers.get("Content-Encoding") == "gzip"
    assert "Accept-Encoding" in resp.headers.get("Vary", "")
    etag = resp.headers.get("ETag", "")
    assert etag.startswith("W/")


def test_no_transform_respected(app: Flask) -> None:
    configure_gzip(app)

    @app.route("/")
    def view():
        resp = jsonify(LARGE_BODY)
        resp.headers["Cache-Control"] = "public, no-transform"
        return resp

    resp = app.test_client().get("/", headers=GZIP_HEADERS)
    assert resp.headers.get("Content-Encoding") is None
