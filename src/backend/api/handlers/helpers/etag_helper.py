import logging
import uuid
from typing import Any, Dict, List, Optional, Set

from flask import request

from backend.common.memcache import MemcacheClient

ETAG_CACHE_TTL: int = 7 * 24 * 3600  # 7 days in seconds


def normalize_etag(etag: Optional[str]) -> Optional[str]:
    """
    Normalizes an ETag string by stripping weak indicators (W/) and quotes.
    """
    if not etag:
        return None
    etag = etag.strip()
    if etag.startswith("W/") or etag.startswith("w/"):
        etag = etag[2:].strip()
    if (etag.startswith('"') and etag.endswith('"')) or (
        etag.startswith("'") and etag.endswith("'")
    ):
        etag = etag[1:-1].strip()
    return etag if etag else None


def get_incoming_etags() -> List[str]:
    """
    Extracts and normalizes all ETags passed in the If-None-Match header.
    """
    etags: List[str] = []
    if_none_match = request.if_none_match
    if if_none_match:
        for e in if_none_match.as_set(include_weak=True):
            norm = normalize_etag(e)
            if norm:
                etags.append(norm)
    if not etags:
        raw_header = request.headers.get("If-None-Match")
        if raw_header:
            for part in raw_header.split(","):
                norm = normalize_etag(part)
                if norm:
                    etags.append(norm)
    return etags


def get_request_path(path: Optional[str] = None) -> str:
    """
    Returns the request path used to scope ETag dependencies in Memcache.
    """
    if path is not None:
        return path.split("?")[0]
    return request.path


def get_etag_dependencies(
    normalized_etag: str, path: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Fetches the query key -> version mapping for an ETag scoped by endpoint path from Memcache.
    """
    try:
        memcache = MemcacheClient.get()
        endpoint_path = get_request_path(path)
        deps = memcache.get(
            f"etag_deps:{endpoint_path}:{normalized_etag}".encode("utf-8")
        )
        if isinstance(deps, dict):
            return deps
    except Exception as e:
        logging.warning(f"Error fetching ETag dependencies from Memcache: {e}")
    return None


def is_etag_valid(normalized_etag: str, path: Optional[str] = None) -> bool:
    """
    Verifies whether all dependent query cache keys for a given ETag match their current versions.
    """
    deps = get_etag_dependencies(normalized_etag, path=path)
    if deps is None or not isinstance(deps, dict) or not deps:
        return False
    try:
        memcache = MemcacheClient.get()
        query_keys = list(deps.keys())
        q_ver_keys = [f"q_ver:{k}".encode("utf-8") for k in query_keys]
        current_versions = memcache.get_multi(q_ver_keys)
        for k, expected_ver in deps.items():
            actual_ver = current_versions.get(f"q_ver:{k}".encode("utf-8"))
            if actual_ver is None or actual_ver != expected_ver:
                return False
        return True
    except Exception as e:
        logging.warning(f"Error validating ETag query versions in Memcache: {e}")
        return False


def save_etag_dependencies(
    normalized_etag: str,
    query_cache_keys: Set[str],
    path: Optional[str] = None,
    ttl: int = ETAG_CACHE_TTL,
) -> None:
    """
    Stores the mapping between an ETag and its dependent query cache keys with their current versions.
    """
    if not query_cache_keys:
        return
    try:
        memcache = MemcacheClient.get()
        endpoint_path = get_request_path(path)
        q_ver_keys = [f"q_ver:{k}".encode("utf-8") for k in query_cache_keys]
        existing_versions = memcache.get_multi(q_ver_keys)
        versions_to_set: Dict[bytes, Any] = {}
        deps: Dict[str, str] = {}
        for k in query_cache_keys:
            q_key = f"q_ver:{k}".encode("utf-8")
            ver = existing_versions.get(q_key)
            if ver is None:
                ver = uuid.uuid4().hex
            # Refresh TTL for existing and new query versions
            versions_to_set[q_key] = ver
            deps[k] = str(ver)

        if versions_to_set:
            memcache.set_multi(versions_to_set, time=ttl)

        memcache.set(
            f"etag_deps:{endpoint_path}:{normalized_etag}".encode("utf-8"),
            deps,
            time=ttl,
        )
    except Exception as e:
        logging.warning(f"Error saving ETag dependencies to Memcache: {e}")
