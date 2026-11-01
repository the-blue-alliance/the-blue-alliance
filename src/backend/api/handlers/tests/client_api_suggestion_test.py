import json
from unittest.mock import patch

from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.client_api_types import (
    EventMatchVideo,
    EventMatchVideosSuggestionMessage,
    EventMatchVideosSuggestionResponse,
    EventMediaSuggestionMessage,
    EventMediaSuggestionResponse,
    MatchVideoSuggestionMessage,
    MatchVideoSuggestionResponse,
    MediaSuggestionMessage,
    TeamSocialMediaSuggestionMessage,
    TeamSocialMediaSuggestionResponse,
    VideoPlaylistMessage,
    VideoPlaylistResponse,
)
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.futures import InstantFuture
from backend.common.helpers.youtube_video_helper import (
    YouTubePlaylistItem,
    YouTubeVideoHelper,
)
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team
from backend.common.models.user import User
from backend.common.suggestions.media_parser import MediaParser
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)


def test_suggest_no_auth(api_client: Client) -> None:
    req = MediaSuggestionMessage(
        reference_type="",
        reference_key="",
        year=2023,
        media_url="",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 401


def test_suggest_bad_reference_type(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    req = MediaSuggestionMessage(
        reference_type="event",
        reference_key="",
        year=2023,
        media_url="",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 400


def test_suggest_bad_year(api_client: Client, mock_clientapi_auth: User) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="",
        year=1800,
        media_url="",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 400


def test_suggest_bad_url(api_client: Client, mock_clientapi_auth: User) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://example.com",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 400


def test_suggest_success(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://imgur.com/ruRAxDm",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 200

    suggestion_id = Suggestion.render_media_key_name(
        2016, "team", "frc1124", "imgur", "ruRAxDm"
    )
    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.author == mock_clientapi_auth.account_key


def test_suggest_already_exists(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    status, _ = SuggestionCreator.createTeamMediaSuggestion(
        none_throws(mock_clientapi_auth.account_key),
        "http://imgur.com/ruRAxDm",
        "frc1124",
        "2016",
    ).get_result()
    assert status == SuggestionCreationStatus.SUCCESS

    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://imgur.com/ruRAxDm",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 304


def test_suggest_keeps_deletehash_private(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://imgur.com/ruRAxDm",
        details_json=json.dumps({"deletehash": "supersecret"}),
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 200

    suggestion_id = Suggestion.render_media_key_name(
        2016, "team", "frc1124", "imgur", "ruRAxDm"
    )
    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None

    suggestion_constents = suggestion.contents
    assert "private_details_json" in suggestion_constents
    assert suggestion_constents["private_details_json"] == json.dumps(
        {"deletehash": "supersecret"}
    )


def _put_event() -> None:
    Event(
        id="2016nyny",
        year=2016,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
    ).put()


def _suggest_event_media(
    api_client: Client, media_url: str, event_key: str = "2016nyny"
) -> EventMediaSuggestionResponse:
    req = EventMediaSuggestionMessage(event_key=event_key, media_url=media_url)
    return make_clientapi_request(
        api_client,
        "/event/media/suggest",
        req,
        EventMediaSuggestionResponse,
    )


def test_suggest_event_media_no_auth(api_client: Client) -> None:
    resp = _suggest_event_media(
        api_client, "https://www.youtube.com/watch?v=H-54KMwMKY0"
    )

    assert (resp["code"], resp["status"]) == (401, "unauthorized")


def test_suggest_event_media_rejects_bad_event_key(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    resp = _suggest_event_media(
        api_client,
        "https://www.youtube.com/watch?v=H-54KMwMKY0",
        "bad-key",
    )

    assert (resp["code"], resp["status"]) == (404, "bad_event")


def test_suggest_event_media_rejects_missing_event(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    resp = _suggest_event_media(
        api_client, "https://www.youtube.com/watch?v=H-54KMwMKY0"
    )

    assert (resp["code"], resp["status"]) == (404, "bad_event")


def test_suggest_event_media_rejects_bad_url(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()

    resp = _suggest_event_media(api_client, "https://example.com/video")

    assert (resp["code"], resp["status"]) == (400, "bad_url")


def test_suggest_event_media_adds_youtube_video(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()

    resp = _suggest_event_media(
        api_client, "https://www.youtube.com/watch?v=H-54KMwMKY0"
    )

    suggestion = Suggestion.get_by_id(
        Suggestion.render_media_key_name(
            2016, "event", "2016nyny", "youtube", "H-54KMwMKY0"
        )
    )
    assert suggestion is not None
    assert (resp["code"], resp["status"], suggestion.author) == (
        200,
        "success",
        mock_clientapi_auth.account_key,
    )


def test_suggest_event_media_adds_smugmug_album(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()
    album = {
        "media_type_enum": MediaType.SMUGMUG_ALBUM,
        "is_social": False,
        "foreign_key": "4RWMLM",
        "site_name": "SmugMug Album",
    }

    with patch.object(MediaParser, "_parse_smugmug", return_value=InstantFuture(album)):
        resp = _suggest_event_media(
            api_client,
            "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE",
        )

    assert (resp["code"], resp["status"]) == (200, "success")


def test_suggest_event_media_reports_pending_suggestion(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()
    media_url = "https://www.youtube.com/watch?v=H-54KMwMKY0"
    _suggest_event_media(api_client, media_url)

    resp = _suggest_event_media(api_client, media_url)

    assert (resp["code"], resp["status"]) == (304, "suggestion_exists")


def test_suggest_event_media_reports_approved_media(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()
    Media(
        id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, "H-54KMwMKY0"),
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="H-54KMwMKY0",
        references=[ndb.Key(Event, "2016nyny")],
        year=2016,
    ).put()

    resp = _suggest_event_media(
        api_client, "https://www.youtube.com/watch?v=H-54KMwMKY0"
    )

    assert (resp["code"], resp["status"]) == (304, "media_exists")


def _put_team() -> None:
    Team(id="frc1124", team_number=1124).put()


def _suggest_team_social_media(
    api_client: Client, media_url: str, team_key: str = "frc1124"
) -> TeamSocialMediaSuggestionResponse:
    req = TeamSocialMediaSuggestionMessage(team_key=team_key, media_url=media_url)
    return make_clientapi_request(
        api_client,
        "/team/social_media/suggest",
        req,
        TeamSocialMediaSuggestionResponse,
    )


def test_suggest_team_social_media_no_auth(api_client: Client) -> None:
    resp = _suggest_team_social_media(api_client, "https://github.com/frc1124")

    assert (resp["code"], resp["status"]) == (401, "unauthorized")


def test_suggest_team_social_media_rejects_bad_team_key(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    resp = _suggest_team_social_media(api_client, "https://github.com/frc1124", "1124")

    assert (resp["code"], resp["status"]) == (404, "bad_team")


def test_suggest_team_social_media_rejects_missing_team(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    resp = _suggest_team_social_media(api_client, "https://github.com/frc1124")

    assert (resp["code"], resp["status"]) == (404, "bad_team")


def test_suggest_team_social_media_rejects_non_social_url(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_team()

    resp = _suggest_team_social_media(api_client, "https://imgur.com/aF8T5ZE")

    assert (resp["code"], resp["status"]) == (400, "bad_url")


def test_suggest_team_social_media_adds_github_profile(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_team()

    resp = _suggest_team_social_media(api_client, "https://github.com/frc1124")

    suggestion = Suggestion.get_by_id(
        Suggestion.render_media_key_name(
            None, "team", "frc1124", "github-profile", "frc1124"
        )
    )
    assert suggestion is not None
    assert (resp["code"], resp["status"], suggestion.author) == (
        200,
        "success",
        mock_clientapi_auth.account_key,
    )


def test_suggest_team_social_media_reports_pending_suggestion(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_team()
    _suggest_team_social_media(api_client, "https://github.com/frc1124")

    resp = _suggest_team_social_media(api_client, "https://github.com/frc1124")

    assert (resp["code"], resp["status"]) == (304, "suggestion_exists")


def test_suggest_team_social_media_reports_approved_media(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_team()
    Media(
        id=Media.render_key_name(MediaType.GITHUB_PROFILE, "frc1124"),
        media_type_enum=MediaType.GITHUB_PROFILE,
        foreign_key="frc1124",
        references=[ndb.Key(Team, "frc1124")],
    ).put()

    resp = _suggest_team_social_media(api_client, "https://github.com/frc1124")

    assert (resp["code"], resp["status"]) == (304, "media_exists")


def _put_match(youtube_videos: list[str] | None = None) -> None:
    Match(
        id="2016nyny_qm1",
        event=ndb.Key(Event, "2016nyny"),
        year=2016,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json="{}",
        youtube_videos=youtube_videos or [],
    ).put()


def _suggest_match_video(
    api_client: Client, youtube_url: str, match_key: str = "2016nyny_qm1"
) -> MatchVideoSuggestionResponse:
    req = MatchVideoSuggestionMessage(match_key=match_key, youtube_url=youtube_url)
    return make_clientapi_request(
        api_client,
        "/match/video/suggest",
        req,
        MatchVideoSuggestionResponse,
    )


def test_suggest_match_video_no_auth(api_client: Client) -> None:
    resp = _suggest_match_video(
        api_client, "https://www.youtube.com/watch?v=H-54KMwMKY0"
    )

    assert (resp["code"], resp["status"]) == (401, "unauthorized")


def test_suggest_match_video_rejects_bad_match_key(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    resp = _suggest_match_video(
        api_client, "https://www.youtube.com/watch?v=H-54KMwMKY0", "2016nyny"
    )

    assert (resp["code"], resp["status"]) == (404, "bad_match")


def test_suggest_match_video_rejects_missing_match(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    resp = _suggest_match_video(
        api_client, "https://www.youtube.com/watch?v=H-54KMwMKY0"
    )

    assert (resp["code"], resp["status"]) == (404, "bad_match")


def test_suggest_match_video_rejects_non_youtube_url(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_match()

    resp = _suggest_match_video(api_client, "https://example.com/video")

    assert (resp["code"], resp["status"]) == (400, "bad_url")


def test_suggest_match_video_adds_youtube_video(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_match()

    resp = _suggest_match_video(api_client, "https://youtu.be/H-54KMwMKY0")

    suggestion = Suggestion.get_by_id(
        Suggestion.render_media_key_name(
            2016, "match", "2016nyny_qm1", "youtube", "H-54KMwMKY0"
        )
    )
    assert suggestion is not None
    assert (resp["code"], resp["status"], suggestion.author) == (
        200,
        "success",
        mock_clientapi_auth.account_key,
    )


def test_suggest_match_video_reports_pending_suggestion(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_match()
    _suggest_match_video(api_client, "https://youtu.be/H-54KMwMKY0")

    resp = _suggest_match_video(api_client, "https://youtu.be/H-54KMwMKY0")

    assert (resp["code"], resp["status"]) == (304, "suggestion_exists")


def test_suggest_match_video_reports_approved_video(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_match(youtube_videos=["H-54KMwMKY0"])

    resp = _suggest_match_video(api_client, "https://youtu.be/H-54KMwMKY0")

    assert (resp["code"], resp["status"]) == (304, "video_exists")


def _resolve_video_playlist(
    api_client: Client, playlist_id: str = "PLabc123"
) -> VideoPlaylistResponse:
    req = VideoPlaylistMessage(playlist_id=playlist_id)
    return make_clientapi_request(
        api_client,
        "/event/video_playlist/resolve",
        req,
        VideoPlaylistResponse,
    )


def test_resolve_video_playlist_no_auth(api_client: Client) -> None:
    resp = _resolve_video_playlist(api_client)

    assert resp["code"] == 401


def test_resolve_video_playlist_rejects_blank_playlist(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    resp = _resolve_video_playlist(api_client, "")

    assert resp["code"] == 400


def test_resolve_video_playlist_returns_videos_with_guessed_matches(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    video = YouTubePlaylistItem(
        video_id="H-54KMwMKY0",
        video_title="Qualification 1 - 2016 New York City Regional",
        guessed_match_partial="qm1",
    )

    with patch.object(
        YouTubeVideoHelper,
        "videos_in_playlist",
        return_value=InstantFuture([video]),
    ):
        resp = _resolve_video_playlist(api_client)

    assert (resp["code"], resp["videos"]) == (200, [video])


def test_resolve_video_playlist_reports_youtube_failure(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    with patch.object(
        YouTubeVideoHelper,
        "videos_in_playlist",
        side_effect=Exception("YouTube API returned 404"),
    ):
        resp = _resolve_video_playlist(api_client)

    assert (resp["code"], resp["videos"]) == (500, [])


def _suggest_event_match_videos(
    api_client: Client, videos: list[EventMatchVideo], event_key: str = "2016nyny"
) -> EventMatchVideosSuggestionResponse:
    req = EventMatchVideosSuggestionMessage(event_key=event_key, videos=videos)
    return make_clientapi_request(
        api_client,
        "/event/match_videos/suggest",
        req,
        EventMatchVideosSuggestionResponse,
    )


def test_suggest_event_match_videos_no_auth(api_client: Client) -> None:
    resp = _suggest_event_match_videos(
        api_client, [EventMatchVideo(video_id="H-54KMwMKY0", match_partial="qm1")]
    )

    assert (resp["code"], resp["status"]) == (401, "unauthorized")


def test_suggest_event_match_videos_rejects_missing_event(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    resp = _suggest_event_match_videos(
        api_client, [EventMatchVideo(video_id="H-54KMwMKY0", match_partial="qm1")]
    )

    assert (resp["code"], resp["status"]) == (404, "bad_event")


def test_suggest_event_match_videos_adds_video_for_event_match(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()
    _put_match()

    _suggest_event_match_videos(
        api_client, [EventMatchVideo(video_id="H-54KMwMKY0", match_partial="qm1")]
    )

    suggestion = Suggestion.get_by_id(
        Suggestion.render_media_key_name(
            2016, "match", "2016nyny_qm1", "youtube", "H-54KMwMKY0"
        )
    )
    assert suggestion is not None
    assert suggestion.author == mock_clientapi_auth.account_key


def test_suggest_event_match_videos_counts_added_suggestions(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()
    _put_match()

    resp = _suggest_event_match_videos(
        api_client,
        [
            EventMatchVideo(video_id="H-54KMwMKY0", match_partial="qm1"),
            EventMatchVideo(video_id="pRaKQ0yCLJY", match_partial="qm2"),
            EventMatchVideo(video_id="MQ0VNzIvHx0", match_partial=""),
        ],
    )

    assert (resp["code"], resp["status"], resp["num_added"]) == (200, "success", 1)


def test_suggest_event_match_videos_skips_pending_suggestions(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    _put_event()
    _put_match()
    videos = [EventMatchVideo(video_id="H-54KMwMKY0", match_partial="qm1")]
    _suggest_event_match_videos(api_client, videos)

    resp = _suggest_event_match_videos(api_client, videos)

    assert resp["num_added"] == 0
