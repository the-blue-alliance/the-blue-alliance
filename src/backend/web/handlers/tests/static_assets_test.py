from pathlib import Path

import pytest
from flask.testing import FlaskClient

from backend.web import static_assets
from backend.web.static_assets import asset_content_hash


@pytest.fixture
def build_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "css").mkdir()
    (tmp_path / "javascript").mkdir()
    (tmp_path / "css" / "main.css").write_text("body {}")
    monkeypatch.setattr(static_assets, "BUILD_DIR", tmp_path)
    return tmp_path


def test_static_asset_served_immutable(
    web_client: FlaskClient, build_dir: Path
) -> None:
    content_hash = asset_content_hash("css/main.css")
    resp = web_client.get(f"/py3_static/{content_hash}/css/main.css")
    assert resp.status_code == 200
    assert resp.data == b"body {}"
    assert resp.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert resp.mimetype == "text/css"
    assert "Set-Cookie" not in resp.headers


def test_static_asset_wrong_hash_redirects_uncached(
    web_client: FlaskClient, build_dir: Path
) -> None:
    content_hash = asset_content_hash("css/main.css")
    resp = web_client.get("/py3_static/0123456789abcdef/css/main.css")
    assert resp.status_code == 302
    assert resp.headers["Location"] == f"/py3_static/{content_hash}/css/main.css"
    assert resp.headers["Cache-Control"] == "no-store"


def test_static_asset_missing_404s(web_client: FlaskClient, build_dir: Path) -> None:
    resp = web_client.get("/py3_static/0123456789abcdef/css/missing.css")
    assert resp.status_code == 404


def test_static_asset_unknown_kind_404s(
    web_client: FlaskClient, build_dir: Path
) -> None:
    resp = web_client.get("/py3_static/0123456789abcdef/images/main.css")
    assert resp.status_code == 404


def test_static_asset_traversal_404s(web_client: FlaskClient, build_dir: Path) -> None:
    (build_dir / "secret.txt").write_text("nope")
    resp = web_client.get("/py3_static/0123456789abcdef/css/..%2Fsecret.txt")
    assert resp.status_code == 404


def test_page_links_hashed_css(web_client: FlaskClient, build_dir: Path) -> None:
    (build_dir / "css" / "tba_combined_style.main.min.css").write_text("a {}")
    content_hash = asset_content_hash("css/tba_combined_style.main.min.css")
    resp = web_client.get("/contact")
    assert resp.status_code == 200
    assert (
        f'href="/py3_static/{content_hash}/css/tba_combined_style.main.min.css"'
        in resp.get_data(as_text=True)
    )
