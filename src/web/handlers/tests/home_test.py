from werkzeug.test import Client


def test_root(web_client: Client) -> None:
    resp = web_client.get("/")
    assert resp.status_code == 200
