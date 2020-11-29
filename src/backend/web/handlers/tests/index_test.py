from werkzeug.test import Client


def test_index(web_client: Client) -> None:
    resp = web_client.get("/")
    assert resp.status_code == 200


def test_about(web_client: Client) -> None:
    resp = web_client.get("/about")
    assert resp.status_code == 200
