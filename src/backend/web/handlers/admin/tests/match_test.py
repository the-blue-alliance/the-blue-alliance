import json

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
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


def store_event(event_key: str = "2019nyny") -> Event:
    event = Event(
        id=event_key,
        event_short=event_key[4:],
        year=int(event_key[:4]),
        event_type_enum=EventType.OFFSEASON,
    )
    event.put()
    return event


# ---------------------------------------------------------------------------
# /admin/matches
# ---------------------------------------------------------------------------


def test_match_dashboard(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.get("/admin/matches")
    assert resp.status_code == 200
    assert b'action="/admin/match/add"' in resp.data


# ---------------------------------------------------------------------------
# /admin/match/edit/<match_key>  (GET)
# ---------------------------------------------------------------------------


def test_match_edit_bad_key(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.get("/admin/match/edit/badkey")
    assert resp.status_code == 404


def test_match_edit_not_found(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.get("/admin/match/edit/2019nyny_qm1")
    assert resp.status_code == 404


def test_match_edit(web_client: Client, login_gae_admin, ndb_stub) -> None:
    store_match()
    resp = web_client.get("/admin/match/edit/2019nyny_qm1")
    assert resp.status_code == 200
    assert b'name="alliances_json"' in resp.data


# ---------------------------------------------------------------------------
# /admin/match/edit/<match_key>  (POST)
# ---------------------------------------------------------------------------


def test_match_edit_post(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_event()
    store_match()

    alliances = {
        "red": {"score": 10, "teams": ["frc11", "frc12", "frc13"]},
        "blue": {"score": 20, "teams": ["frc14", "frc15", "frc16"]},
    }
    breakdown = {"red": {"foo": 1}, "blue": {"foo": 2}}
    resp = web_client.post(
        "/admin/match/edit/2019nyny_qm1",
        data={
            "event_key_name": "2019nyny",
            "set_number": "1",
            "match_number": "1",
            "comp_level": "qm",
            "alliances_json": json.dumps(alliances),
            "score_breakdown_json": json.dumps(breakdown),
            "tba_videos": json.dumps(["tba1"]),
            "youtube_videos": json.dumps(["yt1", "yt2"]),
            "no_auto_update": "True",
            "display_name": "Finals Tiebreaker",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/match/2019nyny_qm1"

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert match.event == ndb.Key(Event, "2019nyny")
    assert match.team_key_names == [
        "frc11",
        "frc12",
        "frc13",
        "frc14",
        "frc15",
        "frc16",
    ]
    assert match.alliances[AllianceColor.RED]["score"] == 10
    assert match.score_breakdown == breakdown
    assert match.tba_videos == ["tba1"]
    assert match.youtube_videos == ["yt1", "yt2"]
    assert match.no_auto_update is True
    assert match.display_name == "Finals Tiebreaker"


def test_match_edit_post_none_values(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    # The edit form renders "None" for unset fields; these must round-trip to None
    store_event()
    store_match()

    alliances = {
        "red": {"score": -1, "teams": ["frc1", "frc2", "frc3"]},
        "blue": {"score": -1, "teams": ["frc4", "frc5", "frc6"]},
    }
    resp = web_client.post(
        "/admin/match/edit/2019nyny_qm1",
        data={
            "event_key_name": "2019nyny",
            "set_number": "1",
            "match_number": "1",
            "comp_level": "qm",
            "alliances_json": json.dumps(alliances),
            "score_breakdown_json": "None",
            "tba_videos": "",
            "youtube_videos": "",
            "display_name": "None",
        },
    )
    assert resp.status_code == 302

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert match.score_breakdown_json is None
    assert match.tba_videos == []
    assert match.youtube_videos == []
    assert match.no_auto_update is False
    assert match.display_name is None


def test_match_edit_post_invalid_breakdown_json(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    # Invalid score breakdown JSON is rejected before anything is written
    store_event()
    store_match()

    resp = web_client.post(
        "/admin/match/edit/2019nyny_qm1",
        data={
            "event_key_name": "2019nyny",
            "set_number": "1",
            "match_number": "1",
            "comp_level": "qm",
            "alliances_json": "{}",
            "score_breakdown_json": "{not json",
        },
    )
    assert resp.status_code == 500

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert match.alliances[AllianceColor.RED]["teams"] == ["frc4", "frc5", "frc6"]


# ---------------------------------------------------------------------------
# /admin/match/delete/<match_key>
# ---------------------------------------------------------------------------


def test_match_delete_get_bad_key(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/match/delete/badkey")
    assert resp.status_code == 404


def test_match_delete_get_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/match/delete/2019nyny_qm1")
    assert resp.status_code == 404


def test_match_delete_get(web_client: Client, login_gae_admin, ndb_stub) -> None:
    store_match()
    resp = web_client.get("/admin/match/delete/2019nyny_qm1")
    assert resp.status_code == 200
    assert b"2019nyny_qm1" in resp.data


def test_match_delete_post_bad_key(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post("/admin/match/delete/badkey")
    assert resp.status_code == 404


def test_match_delete_post_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post("/admin/match/delete/2019nyny_qm1")
    assert resp.status_code == 404


def test_match_delete_post(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_match()
    resp = web_client.post("/admin/match/delete/2019nyny_qm1")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2019nyny"
    assert Match.get_by_id("2019nyny_qm1") is None


# ---------------------------------------------------------------------------
# /admin/match/add
# ---------------------------------------------------------------------------


def test_match_add_event_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/match/add",
        data={"event_key": "2019nyny", "matches_csv": ""},
    )
    assert resp.status_code == 404


def test_match_add(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_event()
    matches_csv = "\n".join(
        [
            "qm1, 1, 2, 3, 4, 5, 6, 10, 20",
            "qm2, 7, 8, 9, 10, 11, 12, ,",
            "sf2m1, 1, 2, 3, 7, 8, 9, 30, 5",
        ]
    )
    resp = web_client.post(
        "/admin/match/add",
        data={"event_key": "2019nyny", "matches_csv": matches_csv},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2019nyny"

    matches = Match.query(Match.event == ndb.Key(Event, "2019nyny")).fetch()
    by_key = {m.key_name: m for m in matches}
    assert set(by_key.keys()) == {"2019nyny_qm1", "2019nyny_qm2", "2019nyny_sf2m1"}

    qm1 = by_key["2019nyny_qm1"]
    assert qm1.year == 2019
    assert qm1.comp_level == CompLevel.QM
    assert qm1.set_number == 1
    assert qm1.match_number == 1
    assert qm1.team_key_names == ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]
    assert qm1.alliances[AllianceColor.RED]["score"] == 10
    assert qm1.alliances[AllianceColor.BLUE]["score"] == 20

    qm2 = by_key["2019nyny_qm2"]
    assert qm2.alliances[AllianceColor.RED]["score"] == -1
    assert qm2.alliances[AllianceColor.BLUE]["score"] == -1

    sf2m1 = by_key["2019nyny_sf2m1"]
    assert sf2m1.comp_level == CompLevel.SF
    assert sf2m1.set_number == 2
    assert sf2m1.match_number == 1


# ---------------------------------------------------------------------------
# /admin/match/override_breakdown
# ---------------------------------------------------------------------------


def test_match_override_score_breakdown_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/match/override_breakdown",
        data={"match_key": "2019nyny_qm1", "new_breakdown": "{}"},
    )
    assert resp.status_code == 404


def test_match_override_score_breakdown(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    store_match()
    breakdown = {"red": {"totalPoints": 5}, "blue": {"totalPoints": 7}}
    resp = web_client.post(
        "/admin/match/override_breakdown",
        data={"match_key": "2019nyny_qm1", "new_breakdown": json.dumps(breakdown)},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2019nyny"

    match = Match.get_by_id("2019nyny_qm1")
    assert match is not None
    assert match.score_breakdown == breakdown
