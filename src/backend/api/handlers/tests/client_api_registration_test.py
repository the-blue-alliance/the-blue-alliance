import json
from unittest.mock import patch

from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.client_api_types import (
    ListDevicesResponse,
    RegisteredMobileClient,
    RegistrationRequest,
)
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.consts.client_type import ClientType
from backend.common.consts.messaging_id_type import MessagingIdType
from backend.common.models.account import Account
from backend.common.models.mobile_client import MobileClient
from backend.common.models.user import User

FID = "cRhMtGRgQ3aPxRPrMVZ0xZ"


def test_register_no_auth(api_client: Client) -> None:
    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="asdf",
        name="Test Device",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 401


def test_register_no_account(
    api_client: Client, mock_clientapi_auth_no_account: None
) -> None:
    """A user with a valid Firebase token but no email should be rejected."""
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
    assert client.messaging_id_type == MessagingIdType.TOKEN


def test_register_android_fcm_client(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    req = RegistrationRequest(
        operating_system="android-fcm",
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
    assert client.client_type == ClientType.OS_ANDROID_FCM
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
            mobile_id_type="token",
        )
    ]


def test_list_clients_fid(api_client: Client, mock_clientapi_auth: User) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(none_throws(mock_clientapi_auth.account_key).id()),
        messaging_id=FID,
        messaging_id_type=MessagingIdType.FID,
        client_type=ClientType.OS_IOS,
        device_uuid="asdf",
        display_name="iPhone",
    ).put()

    resp = make_clientapi_request(api_client, "/list_clients", {}, ListDevicesResponse)
    assert resp["code"] == 200
    assert resp["devices"] == [
        RegisteredMobileClient(
            name="iPhone",
            operating_system="ios",
            mobile_id=FID,
            device_uuid="asdf",
            mobile_id_type="fid",
        )
    ]


def test_list_clients_webhook_omits_mobile_id_type(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(none_throws(mock_clientapi_auth.account_key).id()),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        device_uuid="asdf",
        display_name="Webhook",
    ).put()

    # Not `make_clientapi_request`: safe_json requires every TypedDict key, so it
    # can't load a device that omits the optional `mobile_id_type`
    resp = api_client.post("/clientapi/tbaClient/v9/list_clients", data="{}")
    assert resp.status_code == 200
    assert json.loads(resp.data)["devices"] == [
        RegisteredMobileClient(
            name="Webhook",
            operating_system="webhook",
            mobile_id="https://example.com/webhook",
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


def test_register_collapses_duplicate_token(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    """A re-registration with the same token but a new device_uuid should
    collapse the existing token row instead of creating a duplicate."""
    user_id = str(none_throws(mock_clientapi_auth.account_key).id())
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=user_id,
        messaging_id="abc123",
        client_type=ClientType.WEB,
        device_uuid="old-uuid",
        display_name="Old Device",
    ).put()

    req = RegistrationRequest(
        operating_system="web",
        mobile_id="abc123",
        device_uuid="new-uuid",
        name="New Device",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 304

    user_clients = MobileClient.query(MobileClient.user_id == user_id).fetch()
    assert len(user_clients) == 1
    assert user_clients[0].messaging_id == "abc123"
    assert user_clients[0].device_uuid == "new-uuid"
    assert user_clients[0].display_name == "New Device"


def test_register_fid(api_client: Client, mock_clientapi_auth: User) -> None:
    req = RegistrationRequest(
        operating_system="ios",
        mobile_id=FID,
        device_uuid="asdf",
        name="iPhone",
        mobile_id_type="fid",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 200

    user_clients = MobileClient.query(
        MobileClient.user_id == str(none_throws(mock_clientapi_auth.account_key).id())
    ).fetch()
    assert len(user_clients) == 1
    assert user_clients[0].messaging_id == FID
    assert user_clients[0].messaging_id_type == MessagingIdType.FID


def test_register_unknown_mobile_id_type(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    req = RegistrationRequest(
        operating_system="ios",
        mobile_id=FID,
        device_uuid="asdf",
        name="iPhone",
        mobile_id_type="installation_id",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 400
    assert resp["message"] == "Unknown mobile_id_type: installation_id"

    assert MobileClient.query().fetch() == []


def test_register_non_string_mobile_id_type(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    req = {
        "operating_system": "ios",
        "mobile_id": FID,
        "device_uuid": "asdf",
        "name": "iPhone",
        "mobile_id_type": ["fid"],
    }
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 400

    assert MobileClient.query().fetch() == []


def test_register_fid_for_non_fcm_platform(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    """A FID on a platform that's never sent to must not replace the install's
    FCM token."""
    account_key = none_throws(mock_clientapi_auth.account_key)
    token = f"{FID}:APA91bOld"
    MobileClient(
        parent=account_key,
        user_id=str(account_key.id()),
        messaging_id=token,
        client_type=ClientType.OS_IOS,
        device_uuid="asdf",
        display_name="iPhone",
    ).put()

    req = RegistrationRequest(
        operating_system="web",
        mobile_id=FID,
        device_uuid="asdf",
        name="Browser",
        mobile_id_type="fid",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 400
    assert resp["message"] == "mobile_id_type fid isn't supported for web"

    clients = MobileClient.query(ancestor=account_key).fetch()
    assert [client.messaging_id for client in clients] == [token]


def test_register_existing_fid(api_client: Client, mock_clientapi_auth: User) -> None:
    MobileClient(
        parent=mock_clientapi_auth.account_key,
        user_id=str(none_throws(mock_clientapi_auth.account_key).id()),
        messaging_id=FID,
        messaging_id_type=MessagingIdType.FID,
        client_type=ClientType.OS_IOS,
        device_uuid="asdf",
        display_name="iPhone",
    ).put()

    req = RegistrationRequest(
        operating_system="ios",
        mobile_id=FID,
        device_uuid="asdf",
        name="iPhone",
        mobile_id_type="fid",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 304

    user_clients = MobileClient.query(
        MobileClient.user_id == str(none_throws(mock_clientapi_auth.account_key).id())
    ).fetch()
    assert len(user_clients) == 1
    assert user_clients[0].messaging_id_type == MessagingIdType.FID


def test_register_fid_deletes_replaced_token(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    """Registering a FID deletes this account's FCM token minted for that FID,
    and nothing else."""
    account_key = none_throws(mock_clientapi_auth.account_key)
    replaced_token = f"{FID}:APA91bHun4MxP5egoKMwt2KZFBaFUH-1RYqx"

    def put_client(
        parent: ndb.Key, messaging_id: str, client_type: ClientType
    ) -> ndb.Key:
        return MobileClient(
            parent=parent,
            user_id=str(parent.id()),
            messaging_id=messaging_id,
            client_type=client_type,
            device_uuid="asdf",
            display_name="Device",
        ).put()

    put_client(account_key, replaced_token, ClientType.OS_IOS)
    unrelated_token = put_client(account_key, "otherfid:APA91bOther", ClientType.OS_IOS)
    # Not an FCM client, so not a token for this install
    non_fcm = put_client(account_key, replaced_token, ClientType.WEB)
    other_account = put_client(ndb.Key(Account, "2"), replaced_token, ClientType.OS_IOS)

    req = RegistrationRequest(
        operating_system="ios",
        mobile_id=FID,
        device_uuid="asdf",
        name="iPhone",
        mobile_id_type="fid",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 200

    remaining = {client.key for client in MobileClient.query().fetch()}
    fid_client = MobileClient.query(MobileClient.messaging_id == FID).get()
    assert fid_client is not None
    assert remaining == {unrelated_token, non_fcm, other_account, fid_client.key}


def test_register_fid_keeps_token_when_write_fails(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    """The replaced token is only deleted once the FID is stored, so a failed
    write leaves the device registered."""
    account_key = none_throws(mock_clientapi_auth.account_key)
    token = f"{FID}:APA91bOld"
    MobileClient(
        parent=account_key,
        user_id=str(account_key.id()),
        messaging_id=token,
        client_type=ClientType.OS_IOS,
        device_uuid="asdf",
        display_name="iPhone",
    ).put()

    req = RegistrationRequest(
        operating_system="ios",
        mobile_id=FID,
        device_uuid="asdf",
        name="iPhone",
        mobile_id_type="fid",
    )
    with patch.object(MobileClient, "put", side_effect=RuntimeError("write failed")):
        resp = api_client.post("/clientapi/tbaClient/v9/register", data=json.dumps(req))
    assert resp.status_code == 500

    clients = MobileClient.query(ancestor=account_key).fetch()
    assert [client.messaging_id for client in clients] == [token]


def test_register_token_keeps_other_tokens(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    """Only FID registrations replace tokens; a token registration never deletes."""
    account_key = none_throws(mock_clientapi_auth.account_key)
    MobileClient(
        parent=account_key,
        user_id=str(account_key.id()),
        messaging_id=f"{FID}:APA91bOld",
        client_type=ClientType.OS_IOS,
        device_uuid="asdf",
        display_name="iPhone",
    ).put()

    req = RegistrationRequest(
        operating_system="ios",
        mobile_id=f"{FID}:APA91bNew",
        device_uuid="asdf",
        name="iPhone",
    )
    resp = make_clientapi_request(api_client, "/register", req)
    assert resp["code"] == 200
    assert MobileClient.query(ancestor=account_key).count() == 2
