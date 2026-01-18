from bs4 import BeautifulSoup
from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.web.handlers.match import (
    _build_match_meta_description,
    _format_team_list,
)


def test_format_team_list() -> None:
    assert _format_team_list(["frc254", "frc971", "frc1678"]) == "254, 971, 1678"
    assert _format_team_list(["frc254B", "frc971"]) == "254B, 971"
    assert _format_team_list([]) == ""


def test_build_meta_description_played_blue_wins(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        name="Test Regional",
        event_short="test",
        event_type_enum=0,
        city="Test City",
        state_prov="CA",
        country="USA",
    )
    event.put()

    match = Match(
        id="2024test_qm1",
        event=event.key,
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json='{"red": {"teams": ["frc254", "frc971", "frc1678"], "score": 100}, "blue": {"teams": ["frc118", "frc148", "frc2056"], "score": 120}}',
        team_key_names=["frc254", "frc971", "frc1678", "frc118", "frc148", "frc2056"],
    )

    description = _build_match_meta_description(match, event)
    assert description.startswith("Teams 118, 148, 2056 beat 254, 971, 1678")
    assert "with a score of 120 to 100" in description
    assert "in Quals 1" in description
    assert "at the 2024 Test Regional" in description
    assert "in Test City" in description
    assert description.endswith("Match results and videos.")


def test_build_meta_description_played_red_wins(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        name="Test Regional",
        event_short="test",
        event_type_enum=0,
        city="Test City",
        state_prov="CA",
        country="USA",
    )
    event.put()

    match = Match(
        id="2024test_qm1",
        event=event.key,
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json='{"red": {"teams": ["frc254", "frc971", "frc1678"], "score": 150}, "blue": {"teams": ["frc118", "frc148", "frc2056"], "score": 120}}',
        team_key_names=["frc254", "frc971", "frc1678", "frc118", "frc148", "frc2056"],
    )

    description = _build_match_meta_description(match, event)
    assert "Teams 254, 971, 1678 beat 118, 148, 2056" in description
    assert "with a score of 150 to 120" in description


def test_build_meta_description_played_tie(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        name="Test Regional",
        event_short="test",
        event_type_enum=0,
        city="Test City",
        state_prov="CA",
        country="USA",
    )
    event.put()

    match = Match(
        id="2024test_qm1",
        event=event.key,
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json='{"red": {"teams": ["frc254", "frc971", "frc1678"], "score": 100}, "blue": {"teams": ["frc118", "frc148", "frc2056"], "score": 100}}',
        team_key_names=["frc254", "frc971", "frc1678", "frc118", "frc148", "frc2056"],
    )

    description = _build_match_meta_description(match, event)
    # Red listed first in tie
    assert "Teams 254, 971, 1678 tied 118, 148, 2056" in description
    assert "with a score of 100 to 100" in description


def test_build_meta_description_scheduled(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        name="Test Regional",
        event_short="test",
        event_type_enum=0,
        city="Test City",
        state_prov="CA",
        country="USA",
    )
    event.put()

    match = Match(
        id="2024test_qm1",
        event=event.key,
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json='{"red": {"teams": ["frc254", "frc971", "frc1678"], "score": -1}, "blue": {"teams": ["frc118", "frc148", "frc2056"], "score": -1}}',
        team_key_names=["frc254", "frc971", "frc1678", "frc118", "frc148", "frc2056"],
    )

    description = _build_match_meta_description(match, event)
    assert "Match results and video" not in description
    assert "Teams 254, 971, 1678 vs 118, 148, 2056" in description
    assert "in Quals 1" in description


def test_build_meta_description_unscheduled(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        name="Test Regional",
        event_short="test",
        event_type_enum=0,
        city="Test City",
        state_prov="CA",
        country="USA",
    )
    event.put()

    match = Match(
        id="2024test_qm1",
        event=event.key,
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json='{"red": {"teams": [], "score": -1}, "blue": {"teams": [], "score": -1}}',
        team_key_names=[],
    )

    description = _build_match_meta_description(match, event)
    assert "Quals 1 at the 2024 Test Regional" in description
    assert "FIRST Robotics Competition" in description


def test_get_bad_match_key(web_client: Client) -> None:
    resp = web_client.get("/match/asoudfhsakj")
    assert resp.status_code == 404


def test_get_bad_match_not_exist(web_client: Client) -> None:
    resp = web_client.get("/match/2020nyny_qm1")
    assert resp.status_code == 404


def test_render_match(web_client: Client, setup_full_match) -> None:
    setup_full_match("2019nyny_qm1")

    resp = web_client.get("/match/2019nyny_qm1")
    assert resp.status_code == 200
    assert "max-age=86400" in resp.headers["Cache-Control"]

    soup = BeautifulSoup(resp.data, "html.parser")
    assert (
        " ".join(soup.find(id="match-title").stripped_strings)
        == "Quals 1 New York City Regional 2019"
    )
    assert soup.find(id="match-table-2019nyny_qm1") is not None
    assert soup.find(id="match-breakdown") is not None
    assert soup.find(id="youtube_ooI6fkKfzLc") is not None


@freeze_time("2019-04-04")
def test_render_match_short_cache(web_client: Client, setup_full_match) -> None:
    setup_full_match("2019nyny_qm1")

    resp = web_client.get("/match/2019nyny_qm1")
    assert resp.status_code == 200
    assert "max-age=61" in resp.headers["Cache-Control"]


def test_render_match_meta_description(web_client: Client, setup_full_match) -> None:
    setup_full_match("2019nyny_qm1")

    resp = web_client.get("/match/2019nyny_qm1")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    # Check meta description tag
    meta_desc = soup.find("meta", {"name": "description"})
    assert meta_desc is not None
    content = meta_desc.get("content")
    # Blue won 49-39, so blue teams should be listed first
    assert content.startswith("Teams 1880, 743, 6590 beat 4640, 354, 5599")
    assert "with a score of 49 to 39" in content
    assert "in Quals 1" in content
    assert "2019 New York City Regional" in content
    assert content.endswith("Match results and videos.")

    # Check og:description tag
    og_desc = soup.find("meta", {"property": "og:description"})
    assert og_desc is not None
    assert og_desc.get("content") == content
