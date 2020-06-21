from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.sitevars import apiv3_key


def test_load_page(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap")
    assert resp.status_code == 200


def test_preload_apiv3_key_from_sitevar(
    ndb_client: ndb.Client, local_client: Client
) -> None:
    with ndb_client.context():
        apiv3_key.Apiv3Key.put(apiv3_key.ContentType(apiv3_key="test_apiv3_key"))

    resp = local_client.get("/local/bootstrap")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="apiv3_key")["value"] == "test_apiv3_key"


def test_success_shows_alert(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=success")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    success = soup.find(class_="alert-success")
    assert success is not None


def test_success_shows_alert_with_link(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=success&url=foo")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    success = soup.find(class_="alert-success")
    assert success is not None

    link = success.find("a")
    assert link is not None
    assert link["href"] == "foo"


def test_status_bad_key(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=bad_key")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    error = soup.find(class_="alert-danger")
    assert error is not None
    assert error["data-status"] == "bad_key"


def test_status_bad_apiv3(local_client: Client) -> None:
    resp = local_client.get("/local/bootstrap?status=bad_apiv3")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    error = soup.find(class_="alert-danger")
    assert error is not None
    assert error["data-status"] == "bad_apiv3"


def test_submit_form_no_apiv3(local_client: Client) -> None:
    resp = local_client.post("/local/bootstrap")
    assert resp.status_code == 302

    url = urlparse(resp.headers["Location"])
    assert url.path == "/local/bootstrap"

    query = parse_qs(url.query)
    assert query == {"status": ["bad_apiv3"]}


def test_submit_form_no_key(local_client: Client) -> None:
    resp = local_client.post("/local/bootstrap", data=dict(apiv3_key="test_apiv3_key"))
    assert resp.status_code == 302

    url = urlparse(resp.headers["Location"])
    assert url.path == "/local/bootstrap"

    query = parse_qs(url.query)
    assert query == {"status": ["bad_key"]}


@patch("backend.web.local.bootstrap.LocalDataBootstrap.bootstrap_key")
def test_submit_succeeds(mock_bootstrap, local_client: Client) -> None:
    mock_bootstrap.return_value = "/test"
    resp = local_client.post(
        "/local/bootstrap",
        data={"apiv3_key": "test_apiv3_key", "bootstrap_key": "test"},
    )
    assert resp.status_code == 302

    url = urlparse(resp.headers["Location"])
    assert url.path == "/local/bootstrap"

    query = parse_qs(url.query)
    assert query == {"status": ["success"], "url": ["/test"]}
