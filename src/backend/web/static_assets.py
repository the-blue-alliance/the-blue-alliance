import functools
import hashlib
import os
from pathlib import Path
from typing import Optional

from werkzeug.security import safe_join

# webpack/do_compress output, relative to the app root (src/)
BUILD_DIR = Path(__file__).resolve().parents[2] / "build"

# Unversioned URL prefix for each build subdirectory (static_dir handlers in web.yaml)
LEGACY_STATIC_PREFIXES = {
    "css": "/py3_css",
    "javascript": "/py3_javascript",
}


@functools.lru_cache(maxsize=64)
def _hash_file(path: str, mtime_ns: int, size: int) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def built_asset_path(asset: str) -> Optional[str]:
    kind, _, filename = asset.partition("/")
    if kind not in LEGACY_STATIC_PREFIXES:
        return None
    return safe_join(str(BUILD_DIR / kind), filename)


def asset_content_hash(asset: str) -> Optional[str]:
    """
    Short content hash of a built asset like "css/tba_combined_style.main.min.css",
    or None if it doesn't exist. Keyed on mtime/size so a rebuild (e.g. webpack
    --watch in dev) gets a new hash without a restart.
    """
    path = built_asset_path(asset)
    if path is None:
        return None
    try:
        stat = os.stat(path)
    except OSError:
        return None
    return _hash_file(path, stat.st_mtime_ns, stat.st_size)


def static_asset_url(asset: str) -> str:
    """
    Content-addressed URL for a built asset, served with a one-year immutable
    Cache-Control, so browsers and Cloudflare refetch only when the file changes.
    Falls back to the unversioned URL if the asset hasn't been built.
    """
    content_hash = asset_content_hash(asset)
    if content_hash is None:
        kind, _, filename = asset.partition("/")
        return f"{LEGACY_STATIC_PREFIXES[kind]}/{filename}"
    return f"/py3_static/{content_hash}/{asset}"
