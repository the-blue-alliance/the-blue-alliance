import logging
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Dict, Iterable, List, Optional, TypedDict

import requests

from backend.common.memcache import MemcacheClient
from backend.common.sitevars.smugmug_api_secret import SmugmugApiSecret


class SmugmugPreviewImage(TypedDict):
    thumbnail_url: str
    image_url: str
    web_uri: str


ALBUM_IMAGES_URL = "https://api.smugmug.com/api/v2/album/{}!images"
PREVIEW_IMAGE_COUNT = 8
# Albums are uploaded in shooting order, so the first N photos are usually N
# near-identical frames of the same moment. Fetch a wider window in the one
# request and sample evenly across it for a more representative preview.
PREVIEW_SAMPLE_WINDOW = 48
PREVIEW_CACHE_SECONDS = 6 * 60 * 60
# A failed or timed-out lookup is cached briefly so a flaky album can't make
# every page load wait on it again
PREVIEW_FAILURE_CACHE_SECONDS = 10 * 60
REQUEST_TIMEOUT_SECONDS = 5
# Total wall-clock budget for one batch of lookups; albums that don't come
# back in time get no preview on this request
FETCH_BUDGET_SECONDS = 6
MAX_CONCURRENT_FETCHES = 8
CACHE_KEY_PREFIX = b"smugmug_album_previews:1:"


def _as_dict(value: Any) -> Dict:
    return value if isinstance(value, dict) else {}


def _cache_key(album_key: str) -> bytes:
    return CACHE_KEY_PREFIX + album_key.encode()


def fetch_album_preview_images(
    album_key: str, api_key: str, count: int = PREVIEW_IMAGE_COUNT
) -> Optional[List[SmugmugPreviewImage]]:
    """
    One uncached request for a sample of an album's photos. Returns None on
    any failure (so callers can cache failures for a shorter time than real
    results) and a list, possibly empty, on success. Thread-safe: no ndb.
    """
    url = ALBUM_IMAGES_URL.format(album_key)
    try:
        response = requests.get(
            url,
            params={
                "APIKey": api_key,
                "count": max(count, PREVIEW_SAMPLE_WINDOW),
                "start": 1,
                # Every size URL is individually signed, so sizes only come
                # from this expansion (same as MediaParser's album lookup)
                "_expand": "ImageSizeDetails",
            },
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as e:
        logging.warning(f"SmugMug album images request failed for {album_key}: {e}")
        return None
    if response.status_code != 200:
        logging.warning(
            f"SmugMug album images returned {response.status_code} for {album_key}"
        )
        return None
    try:
        data = _as_dict(response.json())
    except ValueError:
        logging.warning(f"SmugMug album images returned non-JSON for {album_key}")
        return None

    images = _as_dict(data.get("Response")).get("AlbumImage") or []
    if not isinstance(images, list):
        return []
    expansions = _as_dict(data.get("Expansions"))
    previews: List[SmugmugPreviewImage] = []
    for image in images:
        image = _as_dict(image)
        details_uri = _as_dict(_as_dict(image.get("Uris")).get("ImageSizeDetails")).get(
            "Uri"
        )
        sizes = _as_dict(_as_dict(expansions.get(details_uri)).get("ImageSizeDetails"))
        thumbnail_url = image.get("ThumbnailUrl") or ""
        image_url = _as_dict(sizes.get("ImageSizeSmall")).get("Url") or thumbnail_url
        if not thumbnail_url and not image_url:
            continue
        previews.append(
            SmugmugPreviewImage(
                thumbnail_url=thumbnail_url or image_url,
                image_url=image_url,
                web_uri=image.get("WebUri") or "",
            )
        )
    return _sample_evenly(previews, count)


def album_preview_images_many(
    album_keys: Iterable[str],
) -> Dict[str, List[SmugmugPreviewImage]]:
    """
    Preview samples for many albums at once: memcache first, then the misses
    fetched concurrently under a fixed time budget. Every requested key is in
    the result; albums that failed or didn't return in time map to [].

    This exists because a review page lists up to 50 suggestions, and doing
    these lookups one at a time made the first load take over a minute.
    """
    keys = list(dict.fromkeys(k for k in album_keys if k))
    if not keys:
        return {}
    result: Dict[str, List[SmugmugPreviewImage]] = {}

    cache = MemcacheClient.get()
    cached = cache.get_multi([_cache_key(k) for k in keys])
    misses = []
    for key in keys:
        hit = cached.get(_cache_key(key))
        if hit is None:
            misses.append(key)
        else:
            result[key] = hit
    if not misses:
        return result

    api_key = SmugmugApiSecret.api_key()
    if not api_key:
        logging.warning("No SmugMug API key! Configure SmugmugApiSecret sitevar")
        for key in misses:
            result[key] = []
        return result

    fetched: Dict[str, Optional[List[SmugmugPreviewImage]]] = {}
    pool = ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT_FETCHES, len(misses)))
    try:
        futures = {
            pool.submit(fetch_album_preview_images, key, api_key): key for key in misses
        }
        done, not_done = wait(futures, timeout=FETCH_BUDGET_SECONDS)
        for future in done:
            fetched[futures[future]] = future.result()
        if not_done:
            logging.warning(
                "SmugMug album previews timed out for: {}".format(
                    ", ".join(futures[f] for f in not_done)
                )
            )
    finally:
        # Don't wait for stragglers; they finish (or time out) in the background
        pool.shutdown(wait=False, cancel_futures=True)

    successes: Dict[bytes, Any] = {}
    failures: Dict[bytes, Any] = {}
    for key in misses:
        previews = fetched.get(key)
        if previews is None:
            result[key] = []
            failures[_cache_key(key)] = []
        else:
            result[key] = previews
            successes[_cache_key(key)] = previews
    if successes:
        cache.set_multi(successes, time=PREVIEW_CACHE_SECONDS)
    if failures:
        cache.set_multi(failures, time=PREVIEW_FAILURE_CACHE_SECONDS)
    return result


def album_preview_images(album_key: str) -> List[SmugmugPreviewImage]:
    return album_preview_images_many([album_key]).get(album_key, [])


def _sample_evenly(
    items: List[SmugmugPreviewImage], count: int
) -> List[SmugmugPreviewImage]:
    if count <= 0:
        return []
    if len(items) <= count:
        return items
    step = len(items) / count
    return [items[int(i * step)] for i in range(count)]
