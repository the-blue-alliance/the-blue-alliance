from typing import Dict, List
from unittest.mock import Mock, patch

from google.appengine.ext import ndb
from pyre_extensions.refinement import none_throws
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event

AUTH_ID = "playlist_auth_id"
AUTH_SECRET = "playlist_auth_secret"
REQUEST_PATH = "/api/_eventwizard/_playlist/2019nyny/PL123"


def setup_event() -> None:
    Event(
        id="2019nyny",
        year=2019,
        event_short="nyny",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def setup_auth(access_types: List[AuthType]) -> None:
    ApiAuthAccess(
        id=AUTH_ID,
        secret=AUTH_SECRET,
        event_list=[ndb.Key(Event, "2019nyny")],
        auth_types_enum=access_types,
    ).put()


def get_auth_headers(request_path: str, request_body: str) -> Dict[str, str]:
    return {
        "X-TBA-Auth-Id": AUTH_ID,
        "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
            AUTH_SECRET, request_path, request_body
        ),
    }


def test_no_auth(ndb_stub, api_client: Client) -> None:
    setup_event()

    resp = api_client.post(REQUEST_PATH, data="")
    assert resp.status_code == 401


def test_wrong_permission(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.EVENT_TEAMS])

    resp = api_client.post(
        REQUEST_PATH,
        headers=get_auth_headers(REQUEST_PATH, ""),
        data="",
    )

    assert resp.status_code == 401


def test_get_playlist_videos_success(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.MATCH_VIDEO])

    playlist_videos = [
        {
            "video_title": "Qualification 1",
            "video_id": "abc123",
            "guessed_match_partial": "qm1",
        },
        {
            "video_title": "Qualification 2",
            "video_id": "def456",
            "guessed_match_partial": "qm2",
        },
    ]
    mock_future = Mock()
    mock_future.get_result.return_value = playlist_videos

    with patch(
        "backend.api.handlers.eventwizard_internal.YouTubeVideoHelper.videos_in_playlist",
        return_value=mock_future,
    ) as mock_videos_in_playlist:
        resp = api_client.post(
            REQUEST_PATH,
            headers=get_auth_headers(REQUEST_PATH, ""),
            data="",
        )

    assert resp.status_code == 200
    assert resp.json == playlist_videos
    mock_videos_in_playlist.assert_called_once_with("PL123")


def test_get_playlist_videos_failure(ndb_stub, api_client: Client) -> None:
    setup_event()
    setup_auth(access_types=[AuthType.MATCH_VIDEO])

    mock_future = Mock()
    mock_future.get_result.side_effect = Exception("youtube error")

    with patch(
        "backend.api.handlers.eventwizard_internal.YouTubeVideoHelper.videos_in_playlist",
        return_value=mock_future,
    ):
        resp = api_client.post(
            REQUEST_PATH,
            headers=get_auth_headers(REQUEST_PATH, ""),
            data="",
        )

    assert resp.status_code == 500
    assert "Failed to fetch playlist videos" in none_throws(resp.json).get("Error", "")
