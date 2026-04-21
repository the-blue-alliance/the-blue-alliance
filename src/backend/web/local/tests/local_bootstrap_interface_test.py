from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.sitevars import apiv3_key
from backend.common.sitevars import nexus_api_secret


def test_load_page(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap")
    assert resp.status_code == 200


def test_preload_apiv3_key_from_sitevar(ndb_stub, local_client: Client) -> None:
    apiv3_key.Apiv3Key.put(apiv3_key.ContentType(apiv3_key="test_apiv3_key"))

    resp = local_client.get("/local/bootstrap")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="apiv3_key")["value"] == "test_apiv3_key"


def test_preload_nexus_key_from_sitevar(ndb_stub, local_client: Client) -> None:
    nexus_api_secret.NexusApiSecrets.put(
        nexus_api_secret.ContentType(api_secret="test_nexus_key")
    )

    resp = local_client.get("/local/bootstrap")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="nexus_api_key")["value"] == "test_nexus_key"


def test_success_shows_alert(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=success")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    success = soup.find(class_="alert-success")
    assert success is not None


def test_success_shows_alert_with_link(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=success&url=foo")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    success = soup.find(class_="alert-success")
    assert success is not None

    link = success.find("a")
    assert link is not None
    assert link["href"] == "foo"


def test_status_bad_key(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=bad_key")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    error = soup.find(class_="alert-danger")
    assert error is not None
    assert error["data-status"] == "bad_key"


def test_status_bad_apiv3(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=bad_apiv3")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    error = soup.find(class_="alert-danger")
    assert error is not None
    assert error["data-status"] == "bad_apiv3"


def test_submit_form_no_apiv3(local_client: Client) -> None:
    resp = local_client.post("/local/bootstrap")
    assert resp.status_code == 302

    url = urlparse(resp.headers["Location"])
    assert url.path == "/local/bootstrap"

    query = parse_qs(url.query)
    assert query == {"status": ["bad_apiv3"]}


def test_link_nexus_demo_updates_event_and_redirects(
    local_client: Client, taskqueue_stub
) -> None:
    Event(
        id="2026test",
        year=2026,
        event_short="test",
        event_type_enum=EventType.OFFSEASON,
        name="Test Event",
    ).put()

    resp = local_client.post(
        "/local/bootstrap/link_nexus_demo",
        data={
            "test_event_key": "2026test",
            "nexus_demo_event_id": "demoevent",
            "nexus_api_key": "abc123",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/local/bootstrap/nexus/2026test")

    event = Event.get_by_id("2026test")
    assert event is not None
    assert event.nexus_code == "demoevent"


def test_link_nexus_demo_saves_sitevar_if_checked(
    ndb_stub, local_client: Client, taskqueue_stub
) -> None:
    Event(
        id="2026test",
        year=2026,
        event_short="test",
        event_type_enum=EventType.OFFSEASON,
        name="Test Event",
    ).put()

    resp = local_client.post(
        "/local/bootstrap/link_nexus_demo",
        data={
            "test_event_key": "2026test",
            "nexus_demo_event_id": "demoevent",
            "nexus_api_key": "saved_key",
            "save_api_key": "on",
        },
    )
    assert resp.status_code == 302

    assert nexus_api_secret.NexusApiSecrets.auth_token() == "saved_key"


def test_link_nexus_demo_defaults_to_generated_test_event_key(
    local_client: Client, taskqueue_stub
) -> None:
    year = SeasonHelper.get_current_season()
    event_key = f"{year}test"
    Event(
        id=event_key,
        year=year,
        event_short="test",
        event_type_enum=EventType.OFFSEASON,
        name="Test Event",
    ).put()

    resp = local_client.post(
        "/local/bootstrap/link_nexus_demo",
        data={
            "nexus_demo_event_id": "demoevent",
            "nexus_api_key": "abc123",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/local/bootstrap/nexus/{event_key}")

    event = Event.get_by_id(event_key)
    assert event is not None
    assert event.nexus_code == "demoevent"


def test_bootstrap_nexus_page_renders_teams_and_qual_matches(
    ndb_stub, local_client: Client
) -> None:
    year = SeasonHelper.get_current_season()
    event_key = f"{year}test"
    event = Event(
        id=event_key,
        year=year,
        event_short="test",
        event_type_enum=EventType.OFFSEASON,
        name="Test Event",
        nexus_code="demoevent",
    )
    event.put()

    Team(id="frc111", team_number=111, nickname="111").put()
    Team(id="frc222", team_number=222, nickname="222").put()
    Team(id="frc333", team_number=333, nickname="333").put()
    Team(id="frc444", team_number=444, nickname="444").put()
    Team(id="frc555", team_number=555, nickname="555").put()
    Team(id="frc666", team_number=666, nickname="666").put()

    EventTeam(
        id=f"{event_key}_frc111",
        event=event.key,
        team=none_throws(Team.get_by_id("frc111")).key,
        year=year,
    ).put()
    EventTeam(
        id=f"{event_key}_frc222",
        event=event.key,
        team=none_throws(Team.get_by_id("frc222")).key,
        year=year,
    ).put()
    EventTeam(
        id=f"{event_key}_frc333",
        event=event.key,
        team=none_throws(Team.get_by_id("frc333")).key,
        year=year,
    ).put()

    Match(
        id=f"{event_key}_qm1",
        event=event.key,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json='{"blue":{"teams":["frc111","frc222","frc333"],"score":0},"red":{"teams":["frc444","frc555","frc666"],"score":0}}',
        team_key_names=["frc111", "frc222", "frc333", "frc444", "frc555", "frc666"],
        year=year,
        youtube_videos=[],
    ).put()
    Match(
        id=f"{event_key}_sf1m1",
        event=event.key,
        comp_level=CompLevel.SF,
        set_number=1,
        match_number=1,
        alliances_json='{"blue":{"teams":["frc111","frc222","frc333"],"score":0},"red":{"teams":["frc444","frc555","frc666"],"score":0}}',
        team_key_names=["frc111", "frc222", "frc333", "frc444", "frc555", "frc666"],
        year=year,
        youtube_videos=[],
    ).put()

    resp = local_client.get(f"/local/bootstrap/nexus/{event_key}")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    team_link = soup.find("a", href="https://frc.nexus/en/event/demoevent/team-import")
    assert team_link is not None
    match_link = soup.find(
        "a", href="https://frc.nexus/en/event/demoevent/match-import"
    )
    assert match_link is not None
    event_link = soup.find("a", href="https://frc.nexus/en/event/demoevent")
    assert event_link is not None
    pits_link = soup.find("a", href="https://frc.nexus/en/event/demoevent/pits")
    assert pits_link is not None
    queue_link = soup.find("a", href="https://frc.nexus/en/event/demoevent/queue")
    assert queue_link is not None

    pits_button = soup.find("a", href=f"/tasks/get/nexus_pit_locations/{event_key}")
    assert pits_button is not None
    queue_button = soup.find("a", href=f"/tasks/get/nexus_queue_status/{event_key}")
    assert queue_button is not None
    tba_button = soup.find("a", href=f"/event/{event_key}")
    assert tba_button is not None

    copy_buttons = soup.find_all("button", attrs={"data-copy-target": True})
    assert len(copy_buttons) == 2

    textareas = soup.find_all("textarea")
    assert len(textareas) == 2

    teams_text = textareas[0].text
    assert "111" in teams_text
    assert "222" in teams_text
    assert "333" in teams_text

    matches_text = textareas[1].text
    assert "Qualification,1,111,222,333,444,555,666" in matches_text
    assert "sf" not in matches_text.lower()


def test_submit_form_no_key(local_client: Client) -> None:
    resp = local_client.post("/local/bootstrap", data=dict(apiv3_key="test_apiv3_key"))
    assert resp.status_code == 302

    url = urlparse(resp.headers["Location"])
    assert url.path == "/local/bootstrap"

    query = parse_qs(url.query)
    assert query == {"status": ["bad_key"]}


@patch("backend.web.local.bootstrap.LocalDataBootstrap.bootstrap_key")
def test_submit_succeeds(mock_bootstrap, local_client: Client) -> None:
    mock_bootstrap.return_value = "/test"
    resp = local_client.post(
        "/local/bootstrap",
        data={"apiv3_key": "test_apiv3_key", "bootstrap_key": "test"},
    )
    assert resp.status_code == 302

    url = urlparse(resp.headers["Location"])
    assert url.path == "/local/bootstrap"

    query = parse_qs(url.query)
    assert query == {"status": ["success"], "url": ["/test"]}
