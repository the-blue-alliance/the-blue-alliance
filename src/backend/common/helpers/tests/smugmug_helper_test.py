from unittest.mock import Mock, patch

import pytest
import requests

from backend.common.helpers import smugmug_helper
from backend.common.sitevars.smugmug_api_secret import SmugmugApiSecret


@pytest.fixture(autouse=True)
def api_key(monkeypatch: pytest.MonkeyPatch) -> None:
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


def _mock_response(status_code: int = 200, payload: object = None) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=payload)
    return response


def test_album_preview_images() -> None:
    with patch.object(
        smugmug_helper.requests,
        "get",
        return_value=_mock_response(200, _album_images_response()),
    ) as mock_get:
        previews = smugmug_helper.album_preview_images("2HCx3m")

    assert previews == [
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
    url, kwargs = mock_get.call_args[0][0], mock_get.call_args[1]
    assert url == "https://api.smugmug.com/api/v2/album/2HCx3m!images"
    assert kwargs["params"]["APIKey"] == "test-key"
    assert kwargs["params"]["count"] == smugmug_helper.PREVIEW_SAMPLE_WINDOW
    assert kwargs["params"]["_expand"] == "ImageSizeDetails"


def test_album_preview_images_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(SmugmugApiSecret, "api_key", classmethod(lambda cls: None))
    with patch.object(smugmug_helper.requests, "get") as mock_get:
        assert smugmug_helper.album_preview_images("2HCx3m") == []
    mock_get.assert_not_called()


def test_album_preview_images_http_error() -> None:
    with patch.object(
        smugmug_helper.requests, "get", return_value=_mock_response(404, {})
    ):
        assert smugmug_helper.album_preview_images("2HCx3m") == []


def test_album_preview_images_request_exception() -> None:
    with patch.object(
        smugmug_helper.requests,
        "get",
        side_effect=requests.ConnectionError("boom"),
    ):
        assert smugmug_helper.album_preview_images("2HCx3m") == []


def test_album_preview_images_bad_json() -> None:
    response = _mock_response(200)
    response.json = Mock(side_effect=ValueError("not json"))
    with patch.object(smugmug_helper.requests, "get", return_value=response):
        assert smugmug_helper.album_preview_images("2HCx3m") == []


def test_album_preview_images_unexpected_shape() -> None:
    with patch.object(
        smugmug_helper.requests,
        "get",
        return_value=_mock_response(200, {"Response": {"AlbumImage": "nope"}}),
    ):
        assert smugmug_helper.album_preview_images("2HCx3m") == []


def test_album_preview_images_samples_evenly_across_the_window() -> None:
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
        previews = smugmug_helper.album_preview_images("2HCx3m")

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
