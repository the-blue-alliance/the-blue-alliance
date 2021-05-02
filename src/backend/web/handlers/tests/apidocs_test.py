from werkzeug.test import Client


def test_eventwizard2(web_client: Client) -> None:
    resp = web_client.get("eventwizard2")
    assert resp.status_code == 200
