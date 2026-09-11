import logging
from typing import Any, Dict, List, TypedDict

import requests

from backend.common.decorators import memoize
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


def _as_dict(value: Any) -> Dict:
    return value if isinstance(value, dict) else {}


@memoize(timeout=PREVIEW_CACHE_SECONDS)
def album_preview_images(
    album_key: str, count: int = PREVIEW_IMAGE_COUNT
) -> List[SmugmugPreviewImage]:
    """
    The first few photos of a SmugMug album, for previewing an album without
    leaving the page. SmugMug's embed endpoint returns an empty document, so
    this is the only way to show a reviewer what an album actually contains.
    Any failure degrades to an empty list; callers should treat the preview
    as optional.
    """
    api_key = SmugmugApiSecret.api_key()
    if not api_key:
        logging.warning("No SmugMug API key! Configure SmugmugApiSecret sitevar")
        return []
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
            timeout=10,
        )
    except requests.RequestException as e:
        logging.warning(f"SmugMug album images request failed for {album_key}: {e}")
        return []
    if response.status_code != 200:
        logging.warning(
            f"SmugMug album images returned {response.status_code} for {album_key}"
        )
        return []
    try:
        data = _as_dict(response.json())
    except ValueError:
        logging.warning(f"SmugMug album images returned non-JSON for {album_key}")
        return []

    images = _as_dict(data.get("Response")).get("AlbumImage") or []
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


def _sample_evenly(
    items: List[SmugmugPreviewImage], count: int
) -> List[SmugmugPreviewImage]:
    if count <= 0:
        return []
    if len(items) <= count:
        return items
    step = len(items) / count
    return [items[int(i * step)] for i in range(count)]
