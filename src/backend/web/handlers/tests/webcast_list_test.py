import json

from bs4 import BeautifulSoup
from freezegun import freeze_time
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


@freeze_time("2020-04-02")
def test_render_webcast_list(ndb_stub, web_client: Client) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/webcasts")
    assert resp.status_code == 200

    table = BeautifulSoup(resp.data, "html.parser").find("table")
    rows = table.find("tbody").find_all("tr")

    assert len(rows) == 1
    event_row = rows[0]

    assert "".join(event_row.find_all("td")[0].stripped_strings) == "Test Event"
    assert json.loads("".join(event_row.find_all("td")[3].strings)) == [
        {"type": "twitch", "channel": "robosportsnetwork"},
        {"type": "twitch", "channel": "firstinspires"},
    ]
