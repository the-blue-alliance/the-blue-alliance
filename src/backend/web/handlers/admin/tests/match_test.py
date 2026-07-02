from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.comp_level import CompLevel
from backend.common.models.event import Event
from backend.common.models.match import Match


def store_match(youtube_videos=None) -> Match:
    m = Match(
        id="2019nyny_qm1",
        alliances_json='{"blue": {"score": -1, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": -1, "teams": ["frc4", "frc5", "frc6"]}}',
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, "2019nyny"),
        year=2019,
        set_number=1,
        match_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        youtube_videos=youtube_videos or [],
    )
    m.put()
    return m


def test_match_detail(web_client: Client, login_gae_admin, ndb_stub) -> None:
    store_match()
    resp = web_client.get("/admin/match/2019nyny_qm1")
    assert resp.status_code == 200


def test_match_detail_not_found(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.get("/admin/match/2019nyny_qm1")
    assert resp.status_code == 404


def test_match_detail_bad_key(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.get("/admin/match/badkey")
    assert resp.status_code == 404


def test_match_youtube_video_add(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_match()
    resp = web_client.post(
        "/admin/match/youtube/add/2019nyny_qm1",
        data={"youtube_id": "abc123"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/match/2019nyny_qm1"

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert "abc123" in match.youtube_videos


def test_match_youtube_video_add_duplicate(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_match(youtube_videos=["abc123"])
    resp = web_client.post(
        "/admin/match/youtube/add/2019nyny_qm1",
        data={"youtube_id": "abc123"},
    )
    assert resp.status_code == 302

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert match.youtube_videos.count("abc123") == 1


def test_match_youtube_video_add_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/match/youtube/add/2019nyny_qm1",
        data={"youtube_id": "abc123"},
    )
    assert resp.status_code == 404


def test_match_youtube_video_add_bad_key(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/match/youtube/add/badkey",
        data={"youtube_id": "abc123"},
    )
    assert resp.status_code == 404


def test_match_youtube_video_delete(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_match(youtube_videos=["abc123", "xyz789"])
    resp = web_client.post(
        "/admin/match/youtube/delete/2019nyny_qm1",
        data={"youtube_id": "abc123"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/match/2019nyny_qm1"

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert "abc123" not in match.youtube_videos
    assert "xyz789" in match.youtube_videos


def test_match_youtube_video_delete_not_in_list(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_match(youtube_videos=["xyz789"])
    resp = web_client.post(
        "/admin/match/youtube/delete/2019nyny_qm1",
        data={"youtube_id": "notpresent"},
    )
    assert resp.status_code == 302

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert match.youtube_videos == ["xyz789"]


def test_match_youtube_video_delete_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/match/youtube/delete/2019nyny_qm1",
        data={"youtube_id": "abc123"},
    )
    assert resp.status_code == 404


def test_match_youtube_video_delete_bad_key(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/match/youtube/delete/badkey",
        data={"youtube_id": "abc123"},
    )
    assert resp.status_code == 404
