from werkzeug.test import Client


def test_apidocs_trusted_v1(web_client: Client) -> None:
    resp = web_client.get("/apidocs/trusted/v1")
    assert resp.status_code == 200


def test_apidocs_v3(web_client: Client) -> None:
    resp = web_client.get("apidocs/v3")
    assert resp.status_code == 200
