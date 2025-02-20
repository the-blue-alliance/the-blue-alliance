from unittest.mock import patch

from werkzeug.test import Client

from backend.api.client_api_types import (
    PingRequest,
)
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.consts.client_type import ClientType
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.mobile_client import MobileClient
from backend.common.models.user import User


def test_ping_no_auth(api_client: Client) -> None:
    req = PingRequest(
        mobile_id="abc123",
    )
    resp = make_clientapi_request(api_client, "/ping", req)
    assert resp["code"] == 401


def test_ping_no_device(api_client: Client, mock_clientapi_auth: User) -> None:
    req = PingRequest(
        mobile_id="abc123",
    )
    resp = make_clientapi_request(api_client, "/ping", req)
    assert resp["code"] == 404


def test_ping_clinet(api_client: Client, mock_clientapi_auth: User, ndb_stub) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        messaging_id="abc123",
        client_type=ClientType.TEST,
        device_uuid="asdf",
        display_name="Test Device",
    ).put()

    with patch.object(TBANSHelper, "ping") as mock_ping:
        mock_ping.return_value = True
        req = PingRequest(
            mobile_id="abc123",
        )
        resp = make_clientapi_request(api_client, "/ping", req)

    assert resp["code"] == 200


def test_ping_clinet_fails(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        messaging_id="abc123",
        client_type=ClientType.TEST,
        device_uuid="asdf",
        display_name="Test Device",
    ).put()

    with patch.object(TBANSHelper, "ping") as mock_ping:
        mock_ping.return_value = False
        req = PingRequest(
            mobile_id="abc123",
        )
        resp = make_clientapi_request(api_client, "/ping", req)

    assert resp["code"] == 500
