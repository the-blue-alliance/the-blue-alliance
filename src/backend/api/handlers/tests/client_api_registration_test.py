from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.client_api_types import (
    ListDevicesResponse,
    RegisteredMobileClient,
    RegistrationRequest,
)
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.consts.client_type import ClientType
from backend.common.models.mobile_client import MobileClient
from backend.common.models.user import User


def test_register_no_auth(api_client: Client) -> None:
    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="asdf",
        name="Test Device",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 401


def test_register_new_client(api_client: Client, mock_clientapi_auth: User) -> None:
    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="asdf",
        name="Test Device",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 200

    user_clients = MobileClient.query(
        MobileClient.user_id == str(none_throws(mock_clientapi_auth.account_key).id())
    ).fetch()
    assert len(user_clients) == 1

    client = user_clients[0]
    assert client.user_id == "1"
    assert client.messaging_id == "abc123"
    assert client.client_type == ClientType.WEB
    assert client.device_uuid == "asdf"
    assert client.display_name == "Test Device"


def test_register_existing_client(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(none_throws(mock_clientapi_auth.account_key).id()),
        messaging_id="abc123",
        client_type=ClientType.WEB,
        device_uuid="asdf",
        display_name="Test Device",
    ).put()

    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="asdf",
        name="Test Device",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 304

    user_clients = MobileClient.query(
        MobileClient.user_id == str(none_throws(mock_clientapi_auth.account_key).id())
    ).fetch()
    assert len(user_clients) == 1

    client = user_clients[0]
    assert client.user_id == "1"
    assert client.messaging_id == "abc123"
    assert client.client_type == ClientType.WEB
    assert client.device_uuid == "asdf"
    assert client.display_name == "Test Device"


def test_list_clients_no_auth(api_client: Client) -> None:
    resp = make_clientapi_request(api_client, "/list_clients", {}, ListDevicesResponse)
    assert resp["code"] == 401


def test_list_clients(api_client: Client, mock_clientapi_auth: User) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(none_throws(mock_clientapi_auth.account_key).id()),
        messaging_id="abc123",
        client_type=ClientType.WEB,
        device_uuid="asdf",
        display_name="Test Device",
    ).put()

    resp = make_clientapi_request(api_client, "/list_clients", {}, ListDevicesResponse)
    assert resp["code"] == 200
    assert resp["devices"] == [
        RegisteredMobileClient(
            name="Test Device",
            operating_system="web",
            mobile_id="abc123",
            device_uuid="asdf",
        )
    ]


def test_unregister_no_auth(api_client: Client) -> None:
    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="asdf",
        name="Test Device",
    )
    resp = make_clientapi_request(api_client, "/unregister", req)
    assert resp["code"] == 401


def test_unregister_existing_client(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(none_throws(mock_clientapi_auth.account_key).id()),
        messaging_id="abc123",
        client_type=ClientType.WEB,
        device_uuid="asdf",
        display_name="Test Device",
    ).put()

    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="asdf",
        name="Test Device",
    )
    resp = make_clientapi_request(api_client, "/unregister", req)
    assert resp["code"] == 200

    user_clients = MobileClient.query(
        MobileClient.user_id == str(none_throws(mock_clientapi_auth.account_key).id())
    ).fetch()
    assert len(user_clients) == 0


def test_unregister_no_client(api_client: Client, mock_clientapi_auth: User) -> None:
    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="asdf",
        name="Test Device",
    )
    resp = make_clientapi_request(api_client, "/unregister", req)
    assert resp["code"] == 404

    user_clients = MobileClient.query(
        MobileClient.user_id == str(none_throws(mock_clientapi_auth.account_key).id())
    ).fetch()
    assert len(user_clients) == 0
