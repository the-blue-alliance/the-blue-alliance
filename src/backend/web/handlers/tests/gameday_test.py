from werkzeug.test import Client


def test_gameday(web_client: Client) -> None:
    resp = web_client.get("/gameday")
    assert resp.status_code == 200
