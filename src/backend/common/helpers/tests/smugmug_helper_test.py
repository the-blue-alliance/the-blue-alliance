import time
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest
import requests

from backend.common.helpers import smugmug_helper
from backend.common.sitevars.smugmug_api_secret import SmugmugApiSecret


@pytest.fixture(autouse=True)
def setup(memcache_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        SmugmugApiSecret, "api_key", classmethod(lambda cls: "test-key")
    )


def _album_images_response() -> dict:
    return {
        "Response": {
            "AlbumImage": [
                {
                    "ImageKey": "J6Qzk89",
                    "ThumbnailUrl": "https://photos.smugmug.com/a/Th/one-Th.jpg",
                    "WebUri": "https://nefirst.smugmug.com/album/i-J6Qzk89",
                    "Uris": {
                        "ImageSizeDetails": {
                            "Uri": "/api/v2/image/J6Qzk89-0!sizedetails"
                        }
                    },
                },
                {
                    # No expansion for this one: falls back to the thumbnail
                    "ImageKey": "kSV2tvD",
                    "ThumbnailUrl": "https://photos.smugmug.com/a/Th/two-Th.jpg",
                    "WebUri": "https://nefirst.smugmug.com/album/i-kSV2tvD",
                    "Uris": {
                        "ImageSizeDetails": {
                            "Uri": "/api/v2/image/kSV2tvD-0!sizedetails"
                        }
                    },
                },
                {
                    # Nothing usable: skipped
                    "ImageKey": "empty",
                    "Uris": {},
                },
            ]
        },
        "Expansions": {
            "/api/v2/image/J6Qzk89-0!sizedetails": {
                "ImageSizeDetails": {
                    "ImageSizeSmall": {
                        "Url": "https://photos.smugmug.com/a/S/one-S.jpg"
                    },
                    "ImageSizeMedium": {
                        "Url": "https://photos.smugmug.com/a/M/one-M.jpg"
                    },
                }
            }
        },
    }


EXPECTED_PREVIEWS = [
    {
        "thumbnail_url": "https://photos.smugmug.com/a/Th/one-Th.jpg",
        "image_url": "https://photos.smugmug.com/a/S/one-S.jpg",
        "web_uri": "https://nefirst.smugmug.com/album/i-J6Qzk89",
    },
    {
        "thumbnail_url": "https://photos.smugmug.com/a/Th/two-Th.jpg",
        "image_url": "https://photos.smugmug.com/a/Th/two-Th.jpg",
        "web_uri": "https://nefirst.smugmug.com/album/i-kSV2tvD",
    },
]


def _mock_response(status_code: int = 200, payload: Optional[Any] = None) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=payload)
    return response


def test_fetch_album_preview_images() -> None:
    with patch.object(
        smugmug_helper.requests,
        "get",
        return_value=_mock_response(200, _album_images_response()),
    ) as mock_get:
        previews = smugmug_helper.fetch_album_preview_images("2HCx3m", "test-key")

    assert previews == EXPECTED_PREVIEWS
    url, kwargs = mock_get.call_args[0][0], mock_get.call_args[1]
    assert url == "https://api.smugmug.com/api/v2/album/2HCx3m!images"
    assert kwargs["params"]["APIKey"] == "test-key"
    assert kwargs["params"]["count"] == smugmug_helper.PREVIEW_SAMPLE_WINDOW
    assert kwargs["params"]["_expand"] == "ImageSizeDetails"
    assert kwargs["timeout"] == smugmug_helper.REQUEST_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    "response_kwargs",
    [
        {"return_value": _mock_response(404, {})},
        {"side_effect": requests.ConnectionError("boom")},
    ],
)
def test_fetch_album_preview_images_failures_return_none(
    response_kwargs: Dict[str, Any],
) -> None:
    with patch.object(smugmug_helper.requests, "get", **response_kwargs):
        assert smugmug_helper.fetch_album_preview_images("2HCx3m", "k") is None


def test_fetch_album_preview_images_bad_json() -> None:
    response = _mock_response(200)
    response.json = Mock(side_effect=ValueError("not json"))
    with patch.object(smugmug_helper.requests, "get", return_value=response):
        assert smugmug_helper.fetch_album_preview_images("2HCx3m", "k") is None


def test_fetch_album_preview_images_unexpected_shape() -> None:
    with patch.object(
        smugmug_helper.requests,
        "get",
        return_value=_mock_response(200, {"Response": {"AlbumImage": "nope"}}),
    ):
        assert smugmug_helper.fetch_album_preview_images("2HCx3m", "k") == []


def test_fetch_samples_evenly_across_the_window() -> None:
    images = [
        {
            "ImageKey": f"k{i}",
            "ThumbnailUrl": f"https://photos.smugmug.com/a/Th/{i}-Th.jpg",
            "WebUri": f"https://nefirst.smugmug.com/album/i-k{i}",
            "Uris": {},
        }
        for i in range(48)
    ]
    with patch.object(
        smugmug_helper.requests,
        "get",
        return_value=_mock_response(200, {"Response": {"AlbumImage": images}}),
    ):
        previews = smugmug_helper.fetch_album_preview_images("2HCx3m", "k")

    assert previews is not None
    # 8 of 48, spread across the album rather than the first 8 frames
    assert [p["thumbnail_url"].split("/")[-1] for p in previews] == [
        f"{i}-Th.jpg" for i in (0, 6, 12, 18, 24, 30, 36, 42)
    ]


def test_sample_evenly_edge_cases() -> None:
    assert smugmug_helper._sample_evenly([], 8) == []
    one = [
        smugmug_helper.SmugmugPreviewImage(
            thumbnail_url="t", image_url="i", web_uri="w"
        )
    ]
    assert smugmug_helper._sample_evenly(one, 8) == one
    assert smugmug_helper._sample_evenly(one, 0) == []


def test_many_fetches_concurrently_and_caches() -> None:
    with patch.object(
        smugmug_helper.requests,
        "get",
        return_value=_mock_response(200, _album_images_response()),
    ) as mock_get:
        result = smugmug_helper.album_preview_images_many(["a", "b", "a", ""])
        assert result == {"a": EXPECTED_PREVIEWS, "b": EXPECTED_PREVIEWS}
        assert mock_get.call_count == 2  # deduped, one request per album

        # Second call is served entirely from memcache
        again = smugmug_helper.album_preview_images_many(["a", "b"])
        assert again == result
        assert mock_get.call_count == 2

        # A new key alongside cached ones fetches only the new key
        smugmug_helper.album_preview_images_many(["a", "c"])
        assert mock_get.call_count == 3


def test_many_caches_failures_briefly() -> None:
    with patch.object(
        smugmug_helper.requests, "get", return_value=_mock_response(500, {})
    ) as mock_get:
        assert smugmug_helper.album_preview_images_many(["bad"]) == {"bad": []}
        assert smugmug_helper.album_preview_images_many(["bad"]) == {"bad": []}
        assert mock_get.call_count == 1


def test_many_respects_the_time_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smugmug_helper, "FETCH_BUDGET_SECONDS", 0.2)

    def slow_get(*args, **kwargs):
        time.sleep(1.5)
        return _mock_response(200, _album_images_response())

    with patch.object(smugmug_helper.requests, "get", side_effect=slow_get):
        started = time.monotonic()
        result = smugmug_helper.album_preview_images_many(["slow"])
        elapsed = time.monotonic() - started

    assert result == {"slow": []}
    assert elapsed < 1.0  # returned at the budget, not after the request


def test_many_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(SmugmugApiSecret, "api_key", classmethod(lambda cls: None))
    with patch.object(smugmug_helper.requests, "get") as mock_get:
        assert smugmug_helper.album_preview_images_many(["a"]) == {"a": []}
    mock_get.assert_not_called()


def test_many_empty_input() -> None:
    assert smugmug_helper.album_preview_images_many([]) == {}


def test_single_wrapper() -> None:
    with patch.object(
        smugmug_helper.requests,
        "get",
        return_value=_mock_response(200, _album_images_response()),
    ):
        assert smugmug_helper.album_preview_images("a") == EXPECTED_PREVIEWS
