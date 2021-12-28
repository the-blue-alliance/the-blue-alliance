from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.sitevars.gameday_special_webcasts import GamedaySpecialWebcasts
from backend.web.handlers.tests import helpers


def test_gameday(web_client: Client) -> None:
    resp = web_client.get("/gameday")
    assert resp.status_code == 200


def test_alias_redirect(web_client: Client) -> None:
    GamedaySpecialWebcasts.put({"aliases": {"kickoff": "#params"}})

    resp = web_client.get("/watch/kickoff")
    assert resp.status_code == 302
    assert resp.location == "http://localhost/gameday#params"


@freeze_time("2020-03-01")
def test_event_redirect(web_client: Client) -> None:
    GamedaySpecialWebcasts.put({"aliases": {"kickoff": "#params"}})

    event_key = "2020casj"
    helpers.preseed_event(event_key)

    resp = web_client.get(f"/watch/{event_key}")
    assert resp.status_code == 302
    assert (
        resp.location
        == "http://localhost/gameday#layout=1&view_0=2020casj-0&view_1=2020casj-1"
    )


@freeze_time("2020-04-01")
def test_event_redirect_wrong_time(web_client: Client) -> None:
    GamedaySpecialWebcasts.put({"aliases": {"kickoff": "#params"}})

    event_key = "2020casj"
    helpers.preseed_event(event_key)

    resp = web_client.get(f"/watch/{event_key}")
    assert resp.status_code == 302
    assert resp.location == "http://localhost/gameday"


@freeze_time("2020-03-01")
def test_team_redirect(web_client: Client) -> None:
    GamedaySpecialWebcasts.put({"aliases": {"kickoff": "#params"}})

    team_num = 604
    event_key = "2020casj"
    helpers.preseed_team(team_num)
    helpers.preseed_event_for_team(team_num, event_key)

    resp = web_client.get(f"/watch/{team_num}")
    assert resp.status_code == 302
    assert (
        resp.location
        == "http://localhost/gameday#layout=1&view_0=2020casj-0&view_1=2020casj-1"
    )


@freeze_time("2020-04-01")
def test_team_redirect_wrong_time(web_client: Client) -> None:
    GamedaySpecialWebcasts.put({"aliases": {"kickoff": "#params"}})

    team_num = 604
    event_key = "2020casj"
    helpers.preseed_team(team_num)
    helpers.preseed_event_for_team(team_num, event_key)

    resp = web_client.get(f"/watch/{team_num}")
    assert resp.status_code == 302
    assert resp.location == "http://localhost/gameday"


def test_bad_redirect(web_client: Client) -> None:
    GamedaySpecialWebcasts.put({"aliases": {"kickoff": "#params"}})

    resp = web_client.get("/watch/foo")
    assert resp.status_code == 302
    assert resp.location == "http://localhost/gameday"
