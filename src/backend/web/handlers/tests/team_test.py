import pytest
from werkzeug.test import Client


@pytest.mark.usefixtures("ndb_stub")
def test_team_list_no_page(web_client: Client) -> None:
    resp = web_client.get("/teams")
    assert resp.status_code == 200
