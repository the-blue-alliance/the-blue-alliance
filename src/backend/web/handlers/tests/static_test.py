from werkzeug.test import Client


def test_add_data(web_client: Client) -> None:
    resp = web_client.get("/add-data")
    assert resp.status_code == 200


def test_brand(web_client: Client) -> None:
    resp = web_client.get("/brand")
    assert resp.status_code == 200


def test_contact(web_client: Client) -> None:
    resp = web_client.get("/contact")
    assert resp.status_code == 200


def test_bigquery(web_client: Client) -> None:
    resp = web_client.get("/bigquery")
    assert resp.status_code == 302


def test_opr(web_client: Client) -> None:
    resp = web_client.get("/opr")
    assert resp.status_code == 200


def test_privacy(web_client: Client) -> None:
    resp = web_client.get("/privacy")
    assert resp.status_code == 200


def test_swag(web_client: Client) -> None:
    resp = web_client.get("/swag")
    assert resp.status_code == 302
