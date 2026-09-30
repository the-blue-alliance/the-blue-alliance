from werkzeug.test import Client


def test_eventwizard_legacy(web_client: Client) -> None:
    resp = web_client.get("/eventwizard_legacy")
    assert resp.status_code == 200


def test_eventwizard(web_client: Client) -> None:
    resp = web_client.get("/eventwizard")
    assert resp.status_code == 200
