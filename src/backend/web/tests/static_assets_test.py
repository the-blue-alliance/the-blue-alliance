import os
import re
from pathlib import Path

import pytest

from backend.web import static_assets
from backend.web.static_assets import asset_content_hash, static_asset_url


@pytest.fixture
def build_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "css").mkdir()
    (tmp_path / "javascript").mkdir()
    monkeypatch.setattr(static_assets, "BUILD_DIR", tmp_path)
    return tmp_path


def test_static_asset_url_is_content_addressed(build_dir: Path) -> None:
    (build_dir / "css" / "main.css").write_text("body {}")
    url = static_asset_url("css/main.css")
    assert re.fullmatch(r"/py3_static/[0-9a-f]{16}/css/main\.css", url)
    assert static_asset_url("css/main.css") == url


def test_static_asset_url_changes_when_file_changes(build_dir: Path) -> None:
    path = build_dir / "javascript" / "main.js"
    path.write_text("one")
    before = static_asset_url("javascript/main.js")
    path.write_text("two!")
    os.utime(path, ns=(1, 1))
    assert static_asset_url("javascript/main.js") != before


def test_static_asset_url_falls_back_when_not_built(build_dir: Path) -> None:
    assert static_asset_url("css/missing.css") == "/py3_css/missing.css"
    assert static_asset_url("javascript/missing.js") == "/py3_javascript/missing.js"


def test_asset_content_hash_rejects_traversal(build_dir: Path) -> None:
    (build_dir / "secret.txt").write_text("nope")
    assert asset_content_hash("css/../secret.txt") is None
    assert asset_content_hash("other/secret.txt") is None


def test_templates_use_static_asset_url() -> None:
    templates = Path("src/backend/web/templates").rglob("*.html")
    offenders = [
        t
        for t in templates
        if re.search(r"[\"']/?py3_(css|javascript)/", t.read_text())
    ]
    assert offenders == []
