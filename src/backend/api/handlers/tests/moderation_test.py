import json
from datetime import datetime, timedelta
from typing import Any, cast, Dict, List, Optional

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.client_api_auth_helper import ClientApiAuthHelper
from backend.api.handlers.moderation import (
    _find_similar_events,
    _suggested_event_year,
)
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.outgoing_notification_helper import (
    OutgoingNotificationHelper,
)
from backend.common.memcache import MemcacheClient
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.common.models.user import User
from backend.common.sitevars.slack_hook_urls import SlackHookUrls
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)

BASE_URL = "/api/moderation/v1"


@pytest.fixture
def author(ndb_stub) -> Account:
    account = Account(
        id="author_uid",
        email="author@tba.com",
        nickname="Suggestion Author",
        registered=True,
    )
    account.put()
    return account


@pytest.fixture
def moderator(ndb_stub, monkeypatch: pytest.MonkeyPatch):
    """Returns a factory to authenticate future requests as a moderator with
    the given permissions."""

    def _make(
        permissions: List[AccountPermission],
        is_admin: bool = False,
        email_verified: bool = True,
    ) -> User:
        account = Account.get_by_id("moderator_uid")
        if account is None:
            account = Account(
                id="moderator_uid",
                email="moderator@tba.com",
                nickname="Moderator",
                registered=True,
            )
        account.permissions = permissions
        account.put()

        claims: Dict[str, Any] = {
            "email": "moderator@tba.com",
            "uid": "moderator_uid",
            "email_verified": email_verified,
        }
        if is_admin:
            claims["admin"] = True
        user = User(claims)

        monkeypatch.setattr(
            ClientApiAuthHelper, "get_current_user", staticmethod(lambda: user)
        )
        return user

    return _make


@pytest.fixture
def event(ndb_stub) -> Event:
    event = Event(
        id="2016necmp",
        name="New England District Championship",
        event_type_enum=EventType.DISTRICT_CMP,
        short_name="New England",
        event_short="necmp",
        year=2016,
        start_date=datetime(2016, 3, 24),
        end_date=datetime(2016, 3, 27),
        official=False,
        city="Hartford",
        state_prov="CT",
        country="USA",
        webcast_json="",
        website="https://www.firstsv.org",
    )
    event.put()
    return event


@pytest.fixture
def match(ndb_stub, event: Event) -> Match:
    match = Match(
        id="2016necmp_f1m1",
        event=ndb.Key(Event, "2016necmp"),
        year=2016,
        comp_level="f",
        set_number=1,
        match_number=1,
        team_key_names=["frc846", "frc2135", "frc971", "frc254", "frc1678", "frc973"],
        youtube_videos=["JbwUzl3W9ug"],
        alliances_json=json.dumps(
            {
                "blue": {"score": 270, "teams": ["frc846", "frc2135", "frc971"]},
                "red": {"score": 310, "teams": ["frc254", "frc1678", "frc973"]},
            }
        ),
    )
    match.put()
    return match


def create_match_video_suggestion(author: Account) -> str:
    status = SuggestionCreator.createMatchVideoYouTubeSuggestion(
        author.key, "H-54KMwMKY0", "2016necmp_f1m1"
    )
    assert status == SuggestionCreationStatus.SUCCESS
    return Suggestion.render_media_key_name(
        2016, "match", "2016necmp_f1m1", "youtube", "H-54KMwMKY0"
    )


def create_suggestion(
    author: Account,
    target_model: str,
    target_key: Optional[str],
    contents: dict,
    suggestion_id: Optional[str] = None,
) -> str:
    suggestion = Suggestion(
        id=suggestion_id,
        author=author.key,
        target_model=target_model,
        target_key=target_key,
    )
    suggestion.contents = cast(SuggestionDict, contents)
    key = suggestion.put()
    return str(key.id())


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_queue_unauthenticated(api_client: Client) -> None:
    resp = api_client.get(f"{BASE_URL}/queue")
    assert resp.status_code == 401


def test_list_unauthenticated(api_client: Client) -> None:
    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.status_code == 401


def test_accept_unauthenticated(api_client: Client) -> None:
    resp = api_client.post(f"{BASE_URL}/suggestions/abc/accept")
    assert resp.status_code == 401


def test_reject_unauthenticated(api_client: Client) -> None:
    resp = api_client.post(f"{BASE_URL}/suggestions/reject")
    assert resp.status_code == 401


def test_queue_no_permissions(api_client: Client, moderator) -> None:
    moderator([])
    resp = api_client.get(f"{BASE_URL}/queue")
    assert resp.status_code == 403


def test_unverified_email_forbidden(api_client: Client, moderator) -> None:
    # Accounts are linked to tokens by email, so an unverified email must
    # not confer the linked account's permissions — even for admins
    moderator([AccountPermission.REVIEW_MEDIA], email_verified=False)
    resp = api_client.get(f"{BASE_URL}/queue")
    assert resp.status_code == 403

    moderator([], is_admin=True, email_verified=False)
    resp = api_client.post(f"{BASE_URL}/suggestions/abc/accept")
    assert resp.status_code == 403


def test_list_requires_type_permission(api_client: Client, moderator) -> None:
    # REVIEW_MEDIA does not grant access to the offseason event queue
    moderator([AccountPermission.REVIEW_MEDIA])
    resp = api_client.get(f"{BASE_URL}/suggestions/offseason-event")
    assert resp.status_code == 403


def test_list_unknown_type(api_client: Client, moderator) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    resp = api_client.get(f"{BASE_URL}/suggestions/not-a-type")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Queue counts
# ---------------------------------------------------------------------------


def test_queue_counts_filtered_by_permission(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    create_match_video_suggestion(author)

    resp = api_client.get(f"{BASE_URL}/queue")
    assert resp.status_code == 200
    counts = resp.json["counts"]
    assert counts["match"] == 1
    assert counts["media"] == 0
    # REVIEW_MEDIA covers match/media/social-media/event; not these:
    assert "offseason-event" not in counts
    assert "api_auth_access" not in counts
    assert "robot" not in counts
    assert "event_media" not in counts


def test_queue_counts_admin_sees_all(api_client: Client, moderator) -> None:
    moderator([], is_admin=True)
    resp = api_client.get(f"{BASE_URL}/queue")
    assert resp.status_code == 200
    assert set(resp.json["counts"].keys()) == {
        "event",
        "match",
        "media",
        "social-media",
        "offseason-event",
        "api_auth_access",
        "robot",
        "event_media",
    }


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_match_suggestions(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_match_video_suggestion(author)

    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.status_code == 200
    suggestions = resp.json["suggestions"]
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion["key"] == suggestion_id
    assert suggestion["target_key"] == "2016necmp_f1m1"
    assert suggestion["contents"]["youtube_videos"] == ["H-54KMwMKY0"]
    assert suggestion["author"]["nickname"] == "Suggestion Author"
    assert suggestion["author"]["email"] == "author@tba.com"
    assert suggestion["event"]["key"] == "2016necmp"
    assert suggestion["uses_official_webcast_unit"] is False
    assert suggestion["has_first_official_webcast"] is False
    assert resp.json["total"] == 1
    # No YouTube API key configured, so no video metadata
    assert "video_title" not in suggestion


def test_list_total_exceeds_page(
    api_client: Client, moderator, author: Account, event: Event
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    for i in range(3):
        create_suggestion(
            author,
            "event",
            "2016necmp",
            {"webcast_url": f"https://twitch.tv/channel{i}"},
            suggestion_id=f"webcast_{i}",
        )

    resp = api_client.get(f"{BASE_URL}/suggestions/event?limit=2")
    assert resp.status_code == 200
    assert len(resp.json["suggestions"]) == 2
    assert resp.json["total"] == 3


def test_list_author_reputation_counts(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    create_suggestion(
        author,
        "event",
        "2016necmp",
        {"webcast_url": "https://twitch.tv/accepted"},
        suggestion_id="prior_accepted",
    )
    accepted = Suggestion.get_by_id("prior_accepted")
    assert accepted is not None
    accepted.review_state = SuggestionState.REVIEW_ACCEPTED
    accepted.put()
    create_suggestion(
        author,
        "event",
        "2016necmp",
        {"webcast_url": "https://twitch.tv/rejected"},
        suggestion_id="prior_rejected",
    )
    rejected = Suggestion.get_by_id("prior_rejected")
    assert rejected is not None
    rejected.review_state = SuggestionState.REVIEW_REJECTED
    rejected.put()
    create_match_video_suggestion(author)

    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.status_code == 200
    suggestion_author = resp.json["suggestions"][0]["author"]
    assert suggestion_author["accepted_count"] == 1
    assert suggestion_author["rejected_count"] == 1


def test_list_author_reputation_counts_cached(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    create_match_video_suggestion(author)

    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.json["suggestions"][0]["author"]["accepted_count"] == 0

    # A newly accepted suggestion doesn't appear until the hour-long
    # reputation cache expires
    create_suggestion(
        author,
        "event",
        "2016necmp",
        {"webcast_url": "https://twitch.tv/accepted"},
        suggestion_id="accepted_after_cache",
    )
    accepted = Suggestion.get_by_id("accepted_after_cache")
    assert accepted is not None
    accepted.review_state = SuggestionState.REVIEW_ACCEPTED
    accepted.put()

    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.json["suggestions"][0]["author"]["accepted_count"] == 0

    MemcacheClient.get().delete_multi(
        [f"moderation_author_review_counts:{author.key.id()}".encode()]
    )
    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.json["suggestions"][0]["author"]["accepted_count"] == 1


def test_list_match_video_metadata(
    api_client: Client,
    moderator,
    author: Account,
    event: Event,
    match: Match,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.api.handlers import moderation
    from backend.common.sitevars.google_api_secret import GoogleApiSecret

    moderator([AccountPermission.REVIEW_MEDIA])
    create_match_video_suggestion(author)

    monkeypatch.setattr(GoogleApiSecret, "secret_key", staticmethod(lambda: "key"))

    class FakeFuture:
        def get_result(self):
            return {
                "H-54KMwMKY0": {
                    "video_id": "H-54KMwMKY0",
                    "title": "Full Event Stream Day 2",
                    "duration_seconds": 29700,
                }
            }

    monkeypatch.setattr(
        moderation.YoutubeVideoDetailsDatafeed,
        "fetch_async",
        lambda self: FakeFuture(),
    )
    monkeypatch.setattr(
        moderation.YoutubeVideoDetailsDatafeed, "__init__", lambda self, ids: None
    )

    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.status_code == 200
    suggestion = resp.json["suggestions"][0]
    assert suggestion["video_title"] == "Full Event Stream Day 2"
    assert suggestion["video_duration_seconds"] == 29700


def test_list_match_suggestions_first_webcast_flag(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    # Events webcast by FIRST get a stream-rip warning flag
    moderator([AccountPermission.REVIEW_MEDIA])
    event.webcast_json = json.dumps([{"type": "twitch", "channel": "firstinspires12"}])
    event.put()
    create_match_video_suggestion(author)

    resp = api_client.get(f"{BASE_URL}/suggestions/match")
    assert resp.status_code == 200
    assert resp.json["suggestions"][0]["has_first_official_webcast"] is True


def test_list_webcast_suggestions_existing_webcasts(
    api_client: Client, moderator, author: Account, event: Event
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    event.webcast_json = json.dumps([{"type": "twitch", "channel": "tbagameday"}])
    event.put()
    create_suggestion(
        author,
        "event",
        "2016necmp",
        {"webcast_url": "https://twitch.tv/other_channel"},
    )

    resp = api_client.get(f"{BASE_URL}/suggestions/event")
    assert resp.status_code == 200
    suggestion = resp.json["suggestions"][0]
    assert suggestion["existing_webcasts"] == [
        {"type": "twitch", "channel": "tbagameday"}
    ]
    assert suggestion["event"]["start_date"] == "2016-03-24"
    assert suggestion["event"]["end_date"] == "2016-03-27"


def test_list_team_media_suggestions_includes_reference_and_preferred(
    api_client: Client, moderator, author: Account
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    create_suggestion(
        author,
        "media",
        "frc1124",
        {
            "media_type_enum": MediaType.IMGUR,
            "foreign_key": "abc123",
            "reference_type": "team",
            "reference_key": "frc1124",
            "year": 2016,
            "details_json": json.dumps({"image_partial": "abc123_l.jpg"}),
        },
    )

    resp = api_client.get(f"{BASE_URL}/suggestions/media")
    assert resp.status_code == 200
    suggestion = resp.json["suggestions"][0]
    assert suggestion["candidate_media"]["is_image"] is True
    assert suggestion["candidate_media"]["slug_name"] == "imgur"
    assert suggestion["details"]["thumbnail"] == "abc123_m.jpg"
    assert suggestion["existing_preferred"] == []
    assert suggestion["max_preferred"] == Media.MAX_PREFERRED


# ---------------------------------------------------------------------------
# Accept: match video
# ---------------------------------------------------------------------------


def test_accept_match_video(
    api_client: Client,
    moderator,
    author: Account,
    event: Event,
    match: Match,
    taskqueue_stub,
) -> None:
    user = moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_match_video_suggestion(author)

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200
    assert resp.json["result"] == "accepted"
    assert resp.json["created_target_key"] == "2016necmp_f1m1"

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED
    assert suggestion.reviewer == user.account_key

    match = none_throws(Match.get_by_id("2016necmp_f1m1"))
    assert "H-54KMwMKY0" in match.youtube_videos

    audit_logs = AuditLogEntry.query().fetch()
    assert len(audit_logs) == 1
    assert audit_logs[0].account == user.account_key


def test_accept_match_video_new_target_key(
    api_client: Client,
    moderator,
    author: Account,
    event: Event,
    match: Match,
    taskqueue_stub,
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_match_video_suggestion(author)

    match2 = Match(
        id="2016necmp_f1m2",
        event=ndb.Key(Event, "2016necmp"),
        year=2016,
        comp_level="f",
        set_number=1,
        match_number=2,
        team_key_names=["frc846", "frc2135", "frc971", "frc254", "frc1678", "frc973"],
        alliances_json=json.dumps(
            {
                "blue": {"score": 270, "teams": ["frc846", "frc2135", "frc971"]},
                "red": {"score": 310, "teams": ["frc254", "frc1678", "frc973"]},
            }
        ),
    )
    match2.put()

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"target_match_key": "2016necmp_f1m2"},
    )
    assert resp.status_code == 200

    match2 = Match.get_by_id("2016necmp_f1m2")
    assert match2 is not None
    assert "H-54KMwMKY0" in match2.youtube_videos
    match1 = Match.get_by_id("2016necmp_f1m1")
    assert match1 is not None
    assert "H-54KMwMKY0" not in match1.youtube_videos


def test_accept_match_video_bad_target(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_match_video_suggestion(author)

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"target_match_key": "2016necmp_f1m3"},
    )
    assert resp.status_code == 400
    assert resp.json["result"] == "invalid"

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING


def test_accept_twice_conflicts(
    api_client: Client,
    moderator,
    author: Account,
    event: Event,
    match: Match,
    taskqueue_stub,
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_match_video_suggestion(author)

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200
    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 409
    assert resp.json["result"] == "already_reviewed"


def test_accept_not_found(api_client: Client, moderator) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    resp = api_client.post(f"{BASE_URL}/suggestions/nonexistent/accept")
    assert resp.status_code == 404


def test_accept_requires_type_permission(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    # REVIEW_DESIGNS cannot accept a match video suggestion
    moderator([AccountPermission.REVIEW_DESIGNS])
    suggestion_id = create_match_video_suggestion(author)

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 403
    assert resp.json["result"] == "forbidden"


# ---------------------------------------------------------------------------
# Accept: media types
# ---------------------------------------------------------------------------


def test_accept_team_media_with_preferred(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "media",
        "frc1124",
        {
            "media_type_enum": MediaType.IMGUR,
            "foreign_key": "abc123",
            "reference_type": "team",
            "reference_key": "frc1124",
            "year": 2016,
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"set_preferred": True},
    )
    assert resp.status_code == 200

    media = Media.get_by_id("imgur_abc123")
    assert media is not None
    assert media.year == 2016
    team_ref = Media.create_reference("team", "frc1124")
    assert team_ref in media.references
    assert team_ref in media.preferred_references


def test_accept_team_media_honors_default_preferred(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    # When the reviewer doesn't override, the suggester's default_preferred
    # request applies
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "media",
        "frc1124",
        {
            "media_type_enum": MediaType.IMGUR,
            "foreign_key": "abc123",
            "reference_type": "team",
            "reference_key": "frc1124",
            "year": 2016,
            "default_preferred": True,
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200

    media = Media.get_by_id("imgur_abc123")
    assert media is not None
    team_ref = Media.create_reference("team", "frc1124")
    assert team_ref in media.preferred_references


def test_accept_team_media_reviewer_overrides_default_preferred(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "media",
        "frc1124",
        {
            "media_type_enum": MediaType.IMGUR,
            "foreign_key": "abc123",
            "reference_type": "team",
            "reference_key": "frc1124",
            "year": 2016,
            "default_preferred": True,
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"set_preferred": False},
    )
    assert resp.status_code == 200

    media = Media.get_by_id("imgur_abc123")
    assert media is not None
    assert media.preferred_references == []


def test_accept_team_media_year_override(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "media",
        "frc1124",
        {
            "media_type_enum": MediaType.IMGUR,
            "foreign_key": "abc123",
            "reference_type": "team",
            "reference_key": "frc1124",
            "year": 2016,
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept", json={"year": 2017}
    )
    assert resp.status_code == 200

    media = Media.get_by_id("imgur_abc123")
    assert media is not None
    assert media.year == 2017
    assert media.preferred_references == []


def test_accept_team_media_replace_preferred(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    team_ref = Media.create_reference("team", "frc1124")
    existing = Media(
        id="imgur_existing",
        media_type_enum=MediaType.IMGUR,
        foreign_key="existing",
        year=2016,
        references=[team_ref],
        preferred_references=[team_ref],
    )
    existing.put()

    suggestion_id = create_suggestion(
        author,
        "media",
        "frc1124",
        {
            "media_type_enum": MediaType.IMGUR,
            "foreign_key": "abc123",
            "reference_type": "team",
            "reference_key": "frc1124",
            "year": 2016,
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"replace_preferred_media_key": "imgur_existing"},
    )
    assert resp.status_code == 200

    existing = Media.get_by_id("imgur_existing")
    assert existing is not None
    assert team_ref not in existing.preferred_references
    new_media = Media.get_by_id("imgur_abc123")
    assert new_media is not None
    assert team_ref in new_media.preferred_references


def test_accept_social_media(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "social-media",
        "frc1124",
        {
            "media_type_enum": MediaType.GITHUB_PROFILE,
            "foreign_key": "uberasaurus",
            "reference_type": "team",
            "reference_key": "frc1124",
            "is_social": True,
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200

    media = Media.get_by_id("github-profile_uberasaurus")
    assert media is not None
    assert media.year is None


def test_accept_robot_cad(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_DESIGNS])
    suggestion_id = create_suggestion(
        author,
        "robot",
        "frc1124",
        {
            "media_type_enum": MediaType.GRABCAD,
            "foreign_key": "some-model",
            "reference_type": "team",
            "reference_key": "frc1124",
            "year": 2016,
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200
    assert Media.get_by_id("grabcad_some-model") is not None


def test_accept_event_media(
    api_client: Client, moderator, author: Account, event: Event, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_EVENT_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "event_media",
        "2016necmp",
        {
            "media_type_enum": MediaType.YOUTUBE_VIDEO,
            "foreign_key": "H-54KMwMKY0",
            "reference_type": "event",
            "reference_key": "2016necmp",
            "year": 2016,
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200

    media = Media.get_by_id("youtube_H-54KMwMKY0")
    assert media is not None
    assert Media.create_reference("event", "2016necmp") in media.references
    assert media.preferred_references == []


# ---------------------------------------------------------------------------
# Accept: webcast, offseason event, apiwrite
# ---------------------------------------------------------------------------


def test_accept_event_webcast(
    api_client: Client, moderator, author: Account, event: Event, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "event",
        "2016necmp",
        {
            "webcast_url": "https://twitch.tv/frcgamesense",
            "webcast_dict": {"type": "twitch", "channel": "frcgamesense"},
            "webcast_date": "",
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200

    event = none_throws(Event.get_by_id("2016necmp"))
    assert event.webcast == [{"type": "twitch", "channel": "frcgamesense"}]


def test_accept_event_webcast_with_overrides(
    api_client: Client, moderator, author: Account, event: Event, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "event",
        "2016necmp",
        {"webcast_url": "https://somesite.com/stream"},
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"webcast_type": "youtube", "webcast_channel": "someyoutubechannel"},
    )
    assert resp.status_code == 200

    event = none_throws(Event.get_by_id("2016necmp"))
    assert event.webcast == [{"type": "youtube", "channel": "someyoutubechannel"}]


def test_accept_event_webcast_requires_fields(
    api_client: Client, moderator, author: Account, event: Event
) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_suggestion(
        author,
        "event",
        "2016necmp",
        {"webcast_url": "https://somesite.com/stream"},
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 400
    assert resp.json["result"] == "invalid"


def test_accept_offseason_event_requires_dates(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    # Dateless events violate the APIv3 contract and break strict clients
    moderator([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion_id = create_suggestion(
        author,
        "offseason-event",
        None,
        {"name": "Dateless Offseason", "website": "https://example.com"},
        suggestion_id="dateless_offseason",
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"event_short": "dateless"},
    )
    assert resp.status_code == 400
    assert resp.json["result"] == "invalid"
    assert "start_date and end_date are required" in resp.json["message"]

    suggestion = Suggestion.get_by_id("dateless_offseason")
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
    assert Event.query().count() == 0

    # Reviewer-provided dates satisfy the requirement
    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={
            "event_short": "dateless",
            "start_date": "2016-10-01",
            "end_date": "2016-10-02",
        },
    )
    assert resp.status_code == 200
    assert resp.json["result"] == "accepted"
    event = Event.get_by_id("2016dateless")
    assert event is not None
    assert event.start_date is not None


def test_accept_offseason_event(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion_id = create_suggestion(
        author,
        "offseason-event",
        None,
        {
            "name": "The Best Offseason Event",
            "start_date": "2016-10-01",
            "end_date": "2016-10-02",
            "website": "https://example.com",
            "venue_name": "Venue",
            "address": "123 Fake St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"event_short": "bestoff"},
    )
    assert resp.status_code == 200
    assert resp.json["created_target_key"] == "2016bestoff"

    created = Event.get_by_id("2016bestoff")
    assert created is not None
    assert created.name == "The Best Offseason Event"
    assert created.event_type_enum == EventType.OFFSEASON
    assert created.official is False


def test_accept_offseason_event_requires_event_short(
    api_client: Client, moderator, author: Account
) -> None:
    moderator([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion_id = create_suggestion(
        author,
        "offseason-event",
        None,
        {
            "name": "The Best Offseason Event",
            "start_date": "2016-10-01",
            "end_date": "2016-10-02",
            "website": "https://example.com",
            "venue_name": "Venue",
            "address": "123 Fake St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 400

    suggestion = Suggestion.get_by_id(int(suggestion_id))
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING


def test_accept_apiwrite(
    api_client: Client, moderator, author: Account, event: Event, taskqueue_stub
) -> None:
    moderator([AccountPermission.REVIEW_APIWRITE])
    suggestion_id = create_suggestion(
        author,
        "api_auth_access",
        "2016necmp",
        {
            "event_key": "2016necmp",
            "affiliation": "Team 1124",
            "auth_types": [
                int(AuthType.MATCH_VIDEO),
                int(AuthType.EVENT_TEAMS),
            ],
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"auth_types": [int(AuthType.MATCH_VIDEO)], "expiration_days": 30},
    )
    assert resp.status_code == 200
    auth_id = resp.json["created_target_key"]

    auth = ApiAuthAccess.get_by_id(auth_id)
    assert auth is not None
    assert auth.owner == author.key
    assert auth.auth_types_enum == [AuthType.MATCH_VIDEO]
    assert auth.event_list == [ndb.Key(Event, "2016necmp")]
    assert auth.expiration is not None


def test_accept_apiwrite_default_expiration_past_event(
    api_client: Client, moderator, author: Account, event: Event, taskqueue_stub
) -> None:
    # 2016necmp ended long ago, so the default expiration is "never"
    moderator([AccountPermission.REVIEW_APIWRITE])
    suggestion_id = create_suggestion(
        author,
        "api_auth_access",
        "2016necmp",
        {
            "event_key": "2016necmp",
            "affiliation": "Team 1124",
            "auth_types": [int(AuthType.MATCH_VIDEO)],
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200

    auth = ApiAuthAccess.get_by_id(resp.json["created_target_key"])
    assert auth is not None
    assert auth.expiration is None


def test_accept_apiwrite_default_expiration_future_event(
    api_client: Client, moderator, author: Account, taskqueue_stub
) -> None:
    # While event end + 7 days is in the future, default to expiring then
    moderator([AccountPermission.REVIEW_APIWRITE])
    end_date = datetime.now() + timedelta(days=30)
    Event(
        id="2099necmp",
        name="Future District Championship",
        event_type_enum=EventType.DISTRICT_CMP,
        short_name="Future",
        event_short="necmp",
        year=2099,
        start_date=end_date - timedelta(days=2),
        end_date=end_date,
        official=False,
    ).put()
    suggestion_id = create_suggestion(
        author,
        "api_auth_access",
        "2099necmp",
        {
            "event_key": "2099necmp",
            "affiliation": "Team 1124",
            "auth_types": [int(AuthType.MATCH_VIDEO)],
        },
    )

    resp = api_client.post(f"{BASE_URL}/suggestions/{suggestion_id}/accept")
    assert resp.status_code == 200

    auth = ApiAuthAccess.get_by_id(resp.json["created_target_key"])
    assert auth is not None
    assert auth.expiration is not None
    assert auth.expiration == end_date + timedelta(days=8)


def test_accept_apiwrite_sends_admin_alert(
    api_client: Client,
    moderator,
    author: Account,
    event: Event,
    taskqueue_stub,
    monkeypatch,
) -> None:
    moderator([AccountPermission.REVIEW_APIWRITE])
    sent = []
    monkeypatch.setattr(
        SlackHookUrls, "url_for", staticmethod(lambda channel: "http://hook")
    )
    monkeypatch.setattr(
        OutgoingNotificationHelper,
        "send_slack_alert",
        classmethod(lambda cls, url, body: sent.append((url, body))),
    )
    suggestion_id = create_suggestion(
        author,
        "api_auth_access",
        "2016necmp",
        {
            "event_key": "2016necmp",
            "affiliation": "Team 1124",
            "auth_types": [int(AuthType.MATCH_VIDEO)],
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/{suggestion_id}/accept",
        json={"user_message": "Enjoy the keys!"},
    )
    assert resp.status_code == 200

    assert len(sent) == 1
    url, body = sent[0]
    assert url == "http://hook"
    assert "Trusted API Key Request for 2016necmp" in body
    assert "accepted" in body
    assert "Enjoy the keys!" in body
    assert resp.json["created_target_key"] in body


def test_reject_apiwrite_sends_admin_alert(
    api_client: Client, moderator, author: Account, event: Event, monkeypatch
) -> None:
    moderator([AccountPermission.REVIEW_APIWRITE])
    sent = []
    monkeypatch.setattr(
        SlackHookUrls, "url_for", staticmethod(lambda channel: "http://hook")
    )
    monkeypatch.setattr(
        OutgoingNotificationHelper,
        "send_slack_alert",
        classmethod(lambda cls, url, body: sent.append((url, body))),
    )
    suggestion_id = create_suggestion(
        author,
        "api_auth_access",
        "2016necmp",
        {
            "event_key": "2016necmp",
            "affiliation": "Team 1124",
            "auth_types": [int(AuthType.MATCH_VIDEO)],
        },
    )

    resp = api_client.post(
        f"{BASE_URL}/suggestions/reject",
        json={"suggestion_keys": [suggestion_id], "user_message": "Not this one"},
    )
    assert resp.status_code == 200

    assert len(sent) == 1
    url, body = sent[0]
    assert url == "http://hook"
    assert "Trusted API Key Request for 2016necmp" in body
    assert "rejected" in body
    assert "Not this one" in body


# ---------------------------------------------------------------------------
# Similar offseason event matching
# ---------------------------------------------------------------------------


def _offseason_event(key: str, name: str, short_name: str = "") -> Event:
    return Event(
        id=key,
        name=name,
        short_name=short_name or name,
        event_short=key[4:],
        event_type_enum=EventType.OFFSEASON,
        year=int(key[:4]),
    )


def test_find_similar_events_case_insensitive(ndb_stub) -> None:
    events = [_offseason_event("2016cc", "CHEZY CHAMPS")]
    assert _find_similar_events("chezy champs", events) == [
        {"key": "2016cc", "name": "CHEZY CHAMPS"}
    ]


def test_find_similar_events_matches_short_name(ndb_stub) -> None:
    events = [
        _offseason_event(
            "2016bb", "Southern California Robotics Invitational", "Beach Blitz"
        )
    ]
    assert _find_similar_events("Beach Blitz", events) == [
        {"key": "2016bb", "name": "Southern California Robotics Invitational"}
    ]


def test_find_similar_events_containment(ndb_stub) -> None:
    events = [_offseason_event("2016iri", "IROC - Indiana Robotics Off-Season")]
    assert _find_similar_events("IROC", events) == [
        {"key": "2016iri", "name": "IROC - Indiana Robotics Off-Season"}
    ]


def test_find_similar_events_excludes_dissimilar(ndb_stub) -> None:
    events = [_offseason_event("2016cc", "Chezy Champs")]
    assert _find_similar_events("Ranger Rumble", events) == []


def test_find_similar_events_strongest_first_and_capped(ndb_stub) -> None:
    events = [
        _offseason_event(f"2016ev{i}", f"Chezy Champs Qualifier {i}") for i in range(6)
    ]
    events.append(_offseason_event("2016cc", "Chezy Champs"))
    results = _find_similar_events("Chezy Champs", events)
    assert len(results) == 5
    assert results[0] == {"key": "2016cc", "name": "Chezy Champs"}


def test_suggested_event_year(ndb_stub) -> None:
    suggestion = Suggestion()
    suggestion.contents = cast(SuggestionDict, {"start_date": "2027-10-01"})
    assert _suggested_event_year(suggestion) == 2027

    suggestion = Suggestion()
    suggestion.contents = cast(SuggestionDict, {"start_date": "sometime"})
    assert _suggested_event_year(suggestion) == datetime.now().year


# ---------------------------------------------------------------------------
# Reject
# ---------------------------------------------------------------------------


def test_reject_batch(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    user = moderator([AccountPermission.REVIEW_MEDIA])
    suggestion_id = create_match_video_suggestion(author)

    resp = api_client.post(
        f"{BASE_URL}/suggestions/reject",
        json={"suggestion_keys": [suggestion_id, "nonexistent"]},
    )
    assert resp.status_code == 200
    results = {r["suggestion_key"]: r["result"] for r in resp.json["results"]}
    assert results[suggestion_id] == "rejected"
    assert results["nonexistent"] == "not_found"

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_REJECTED
    assert suggestion.reviewer == user.account_key

    # No video was added
    match = none_throws(Match.get_by_id("2016necmp_f1m1"))
    assert "H-54KMwMKY0" not in match.youtube_videos


def test_reject_requires_body(api_client: Client, moderator) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    resp = api_client.post(f"{BASE_URL}/suggestions/reject", json={})
    assert resp.status_code == 400


def test_reject_requires_type_permission(
    api_client: Client, moderator, author: Account, event: Event, match: Match
) -> None:
    # REVIEW_DESIGNS cannot reject a match video suggestion; the write path
    # re-checks per-suggestion permissions independently of the read path
    moderator([AccountPermission.REVIEW_DESIGNS])
    suggestion_id = create_match_video_suggestion(author)

    resp = api_client.post(
        f"{BASE_URL}/suggestions/reject", json={"suggestion_keys": [suggestion_id]}
    )
    assert resp.status_code == 200
    results = {r["suggestion_key"]: r["result"] for r in resp.json["results"]}
    assert results[suggestion_id] == "forbidden"

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING


def test_reject_batch_capped(api_client: Client, moderator) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    resp = api_client.post(
        f"{BASE_URL}/suggestions/reject",
        json={"suggestion_keys": [str(i) for i in range(501)]},
    )
    assert resp.status_code == 400


def test_list_clamps_negative_limit(api_client: Client, moderator) -> None:
    moderator([AccountPermission.REVIEW_MEDIA])
    resp = api_client.get(f"{BASE_URL}/suggestions/match?limit=-5")
    assert resp.status_code == 200
    assert resp.json["suggestions"] == []
