import json
from typing import Any, Dict, Optional

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.web.handlers.admin.score_breakdown_alliance_key import (
    strip_stray_alliance_key,
)

ALLIANCES = {
    "red": {"teams": ["frc1", "frc2", "frc3"], "score": 100},
    "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 90},
}


def _breakdown(color: str, with_key: bool) -> dict:
    b: Dict[str, Any] = {"totalPoints": 100 if color == "red" else 90, "foulPoints": 5}
    if with_key:
        b["alliance"] = color.capitalize()
    return b


def _put_match(
    event_key: str,
    number: int,
    with_key: bool = True,
    no_auto_update: bool = False,
    breakdown_json: Optional[str] = None,
) -> str:
    key = f"{event_key}_sf{number}m1"
    if breakdown_json is None:
        breakdown_json = json.dumps(
            {c: _breakdown(c, with_key) for c in ("red", "blue")}
        )
    Match(
        id=key,
        event=ndb.Key(Event, event_key),
        year=2025,
        comp_level="sf",
        set_number=number,
        match_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=json.dumps(ALLIANCES),
        score_breakdown_json=breakdown_json,
        youtube_videos=["abc123"],
        no_auto_update=no_auto_update,
    ).put()
    ndb.get_context().clear_cache()
    return key


def _stored(key: str) -> Match:
    match = Match.get_by_id(key, use_cache=False, use_memcache=False)
    assert match is not None
    return match


def _stored_breakdown(key: str) -> dict:
    return json.loads(_stored(key).score_breakdown_json or "{}")


def test_dashboard_requires_admin(web_client: Client) -> None:
    assert web_client.get("/admin/score_breakdown_alliance_key").status_code == 401


def test_dashboard_requires_admin_not_user(web_client: Client, login_gae_user) -> None:
    assert web_client.get("/admin/score_breakdown_alliance_key").status_code == 401


def test_strip_requires_admin(web_client: Client) -> None:
    resp = web_client.post("/admin/score_breakdown_alliance_key/strip")
    assert resp.status_code == 401


def test_strip_requires_admin_not_user(web_client: Client, login_gae_user) -> None:
    resp = web_client.post("/admin/score_breakdown_alliance_key/strip")
    assert resp.status_code == 401


def test_dashboard_lists_affected_matches(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    affected = _put_match("2025bc", 1)
    clean = _put_match("2025bc", 2, with_key=False)

    resp = web_client.get("/admin/score_breakdown_alliance_key")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Matches with the key: 1" in body
    assert affected in body
    assert clean not in body


def test_strip_post_cleans_and_redirects(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    key = _put_match("2025bc", 1)

    resp = web_client.post("/admin/score_breakdown_alliance_key/strip")

    assert resp.status_code == 302
    assert "alliance" not in _stored_breakdown(key)["red"]


def test_strip_removes_only_the_alliance_key(ndb_stub, taskqueue_stub) -> None:
    key = _put_match("2025bc", 1)

    assert [m.key_name for m in strip_stray_alliance_key()] == [key]

    assert _stored_breakdown(key) == {
        c: _breakdown(c, with_key=False) for c in ("red", "blue")
    }


def test_strip_keeps_other_match_fields(ndb_stub, taskqueue_stub) -> None:
    key = _put_match("2025bc", 1, no_auto_update=True)

    strip_stray_alliance_key()

    match = _stored(key)
    assert match.no_auto_update is True
    assert match.youtube_videos == ["abc123"]
    assert json.loads(match.alliances_json) == ALLIANCES
    assert match.team_key_names == ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]


def test_strip_ignores_other_events(ndb_stub, taskqueue_stub) -> None:
    other = _put_match("2025casj", 1)

    assert strip_stray_alliance_key() == []

    assert _stored_breakdown(other)["red"]["alliance"] == "Red"


def test_strip_skips_matches_without_the_key(ndb_stub, taskqueue_stub) -> None:
    clean = _put_match("2025bc", 1, with_key=False)
    before = _stored(clean).updated

    assert strip_stray_alliance_key() == []

    assert _stored(clean).updated == before


def test_strip_tolerates_missing_or_bad_breakdowns(ndb_stub, taskqueue_stub) -> None:
    _put_match("2025bc", 1, breakdown_json="not json")
    _put_match("2025bc", 2, breakdown_json="null")

    assert strip_stray_alliance_key() == []


def test_rerun_is_noop(ndb_stub, taskqueue_stub) -> None:
    _put_match("2025bc", 1)
    strip_stray_alliance_key()

    assert strip_stray_alliance_key() == []
