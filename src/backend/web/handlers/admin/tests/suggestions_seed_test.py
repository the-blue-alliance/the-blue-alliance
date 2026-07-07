from werkzeug.test import Client

from backend.common.consts.account_permission import SUGGESTION_PERMISSIONS
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SUGGESTION_TYPES
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team
from backend.web.handlers.admin.suggestions_seed import (
    SEED_EVENT_NAME,
    SEED_IMGUR_IMAGE_ID,
    SEED_INSTAGRAM_POST_ID,
    SEED_TEAM_NICKNAME,
    SEED_TWITCH_CHANNEL,
    SEED_YOUTUBE_VIDEO_ID,
)


def test_seed_page_requires_admin(web_client: Client) -> None:
    resp = web_client.get("/admin/suggestions/seed")
    assert resp.status_code == 401


def test_seed_page_renders(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/suggestions/seed")
    assert resp.status_code == 200
    assert b"Seed Suggestions" in resp.data


def test_seed_all_types(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/suggestions/seed",
        data={
            "types": SUGGESTION_TYPES,
            "team_key": "frc2",
            "event_key": "2020np",
            "match_key": "2020np_qm1",
        },
    )
    assert resp.status_code == 200

    # Target entities were created as the mocked data team/event
    team = Team.get_by_id("frc2")
    assert team is not None
    assert team.nickname == SEED_TEAM_NICKNAME
    event = Event.get_by_id("2020np")
    assert event is not None
    assert event.name == SEED_EVENT_NAME
    match = Match.get_by_id("2020np_qm1")
    assert match is not None
    assert "frc2" in match.team_key_names

    # One pending suggestion of every type exists
    suggestions = Suggestion.query(
        Suggestion.review_state == SuggestionState.REVIEW_PENDING
    ).fetch()
    seeded_types = {s.target_model for s in suggestions}
    assert seeded_types == set(SUGGESTION_TYPES)


def test_seed_is_repeatable(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    for _ in range(2):
        resp = web_client.post(
            "/admin/suggestions/seed",
            data={
                "types": ["media", "match", "offseason-event"],
                "team_key": "frc2",
                "event_key": "2020np",
                "match_key": "2020np_qm1",
            },
        )
        assert resp.status_code == 200

    suggestions = Suggestion.query(
        Suggestion.review_state == SuggestionState.REVIEW_PENDING
    ).fetch()
    by_type = {}
    for s in suggestions:
        by_type.setdefault(s.target_model, []).append(s)
    # Each media seeding creates an image, a video, and an instagram photo
    assert len(by_type["media"]) == 6
    assert len(by_type["match"]) == 2
    assert len(by_type["offseason-event"]) == 2


def test_seed_uses_real_media_examples(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/suggestions/seed",
        data={
            "types": ["match", "event_media", "event", "media"],
            "team_key": "frc2",
            "event_key": "2020np",
            "match_key": "2020np_qm1",
        },
    )
    assert resp.status_code == 200

    suggestions = Suggestion.query(
        Suggestion.review_state == SuggestionState.REVIEW_PENDING
    ).fetch()
    by_type = {}
    for s in suggestions:
        by_type.setdefault(s.target_model, []).append(s)
    assert by_type["match"][0].contents["youtube_videos"] == [SEED_YOUTUBE_VIDEO_ID]
    assert by_type["event_media"][0].contents["foreign_key"] == SEED_YOUTUBE_VIDEO_ID
    assert (
        by_type["event"][0].contents["webcast_dict"]["channel"] == SEED_TWITCH_CHANNEL
    )
    media_foreign_keys = {s.contents["foreign_key"] for s in by_type["media"]}
    assert media_foreign_keys == {
        SEED_IMGUR_IMAGE_ID,
        SEED_YOUTUBE_VIDEO_ID,
        SEED_INSTAGRAM_POST_ID,
    }


def test_grant_permissions(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    Account(id="mod_uid", email="mod@example.com", registered=True).put()

    resp = web_client.post(
        "/admin/suggestions/seed",
        data={"grant_email": "mod@example.com"},
    )
    assert resp.status_code == 200

    account = Account.get_by_id("mod_uid")
    assert account is not None
    assert set(account.permissions) == SUGGESTION_PERMISSIONS


def test_seed_blocked_in_prod(web_client: Client, login_gae_admin) -> None:
    # Seeding fabricates data and grants permissions; it must 404 in prod
    # even for GAE admins. The GAE request middleware rebuilds os.environ
    # from the WSGI environ, so GAE_ENV is injected per-request here (as
    # the production runtime does) rather than via monkeypatch.setenv.
    prod_environ = {"GAE_ENV": "standard"}

    resp = web_client.get("/admin/suggestions/seed", environ_overrides=prod_environ)
    assert resp.status_code == 404

    resp = web_client.post(
        "/admin/suggestions/seed",
        data={"types": ["match"]},
        environ_overrides=prod_environ,
    )
    assert resp.status_code == 404
