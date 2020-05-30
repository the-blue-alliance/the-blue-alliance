from werkzeug.test import Client


def test_root(default_client: Client) -> None:
    resp = default_client.get("/")
    assert resp.status_code == 404
