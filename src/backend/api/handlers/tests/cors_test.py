import pytest
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event


@pytest.fixture(autouse=True)
def setup_event(ndb_stub) -> None:
    Event(
        id="2019nyny",
        year=2019,
        event_short="nyny",
        event_type_enum=EventType.OFFSEASON,
    ).put()


def test_api_trusted_options_expected_headers(api_client: Client) -> None:
    origin = "https://www.thebluealliance.com"
    method = "POST"
    headers = ", ".join(["Content-Type", "X-TBA-Auth-Id", "X-TBA-Auth-Sig"])
    resp = api_client.options(
        "/api/trusted/v1/event/2019nyny/team_list/update",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert method in resp.headers["Allow"]
    assert resp.headers["Access-Control-Allow-Origin"] == origin
    assert resp.headers["Access-Control-Allow-Headers"] == headers


def test_api_trusted_options_cross_origin(api_client: Client) -> None:
    origin = "https://www.somewhere-else.com"
    method = "POST"
    headers = ", ".join(["X-TBA-Auth-Id", "X-TBA-Something-Else"])
    resp = api_client.options(
        "/api/trusted/v1/event/2019nyny/team_list/update",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == origin


def test_api_trusted_options_wrong_method(api_client: Client) -> None:
    origin = "https://www.thebluealliance.com"
    method = "GET"
    headers = ", ".join(["Content-Type", "X-TBA-Auth-Id", "X-TBA-Auth-Sig"])
    resp = api_client.options(
        "/api/trusted/v1/event/2019nyny/team_list/update",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert method not in resp.headers["Allow"]


def test_api_trusted_options_bad_headers(api_client: Client) -> None:
    origin = "https://www.thebluealliance.com"
    method = "POST"
    headers = ", ".join(["X-TBA-Auth-Id", "X-TBA-Something-Else"])
    resp = api_client.options(
        "/api/trusted/v1/event/2019nyny/team_list/update",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Headers"] == "X-TBA-Auth-Id"


def test_apiv3_options_expected_headers(api_client: Client) -> None:
    origin = "https://www.thebluealliance.com"
    method = "GET"
    headers = ", ".join(["X-TBA-Auth-Key"])
    resp = api_client.options(
        "/api/v3/team/frc254",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert method in resp.headers["Allow"]
    assert resp.headers["Access-Control-Allow-Origin"] == origin
    assert resp.headers["Access-Control-Allow-Headers"] == headers


def test_apiv3_options_cross_origin(api_client: Client) -> None:
    origin = "https://www.somewhere-else.com"
    method = "GET"
    headers = ", ".join(["X-TBA-Auth-Key"])
    resp = api_client.options(
        "/api/v3/team/frc254",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == origin


def test_apiv3_options_wrong_method(api_client: Client) -> None:
    origin = "https://www.thebluealliance.com"
    method = "POST"
    headers = ", ".join(["X-TBA-Auth-Key"])
    resp = api_client.options(
        "/api/v3/team/frc254",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert method not in resp.headers["Allow"]


def test_apiv3_options_bad_headers(api_client: Client) -> None:
    origin = "https://www.thebluealliance.com"
    method = "GET"
    headers = ", ".join(["X-TBA-Auth-Key", "X-TBA-Something-Else"])
    resp = api_client.options(
        "/api/v3/team/frc254",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )

    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Headers"] == "X-TBA-Auth-Key"
