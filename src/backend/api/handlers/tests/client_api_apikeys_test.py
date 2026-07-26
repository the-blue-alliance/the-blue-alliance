import datetime
from typing import cast
from unittest.mock import Mock

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.client_api_types import (
    AddApiReadKeyMessage,
    AddApiReadKeyResponse,
    ApiKeysResponse,
    ApiReadKeyMessage,
    ApiWriteKeyMessage,
    DeleteApiReadKeyMessage,
    VoidRequest,
)
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.user import User


def test_list_api_keys_no_auth(
    api_client: Client, mock_clientapi_auth_no_account: None
) -> None:
    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/api_keys/list", req)
    assert resp["code"] == 401


def test_list_api_keys_empty(api_client: Client, mock_clientapi_auth: User) -> None:
    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/api_keys/list", req, ApiKeysResponse)
    assert resp == ApiKeysResponse(code=200, message="", read_keys=[], write_keys=[])


def test_list_api_keys(api_client: Client, mock_clientapi_auth: User) -> None:
    mock = cast(Mock, mock_clientapi_auth)
    created = datetime.datetime(2023, 1, 2, 3, 4, 5)
    expiration = datetime.datetime(2023, 6, 7, 8, 9, 10)
    mock.api_read_keys = [
        ApiAuthAccess(
            id="readkey123",
            auth_types_enum=[AuthType.READ_API],
            description="my read key",
            created=created,
        )
    ]
    mock.api_write_keys = [
        ApiAuthAccess(
            id="writekey456",
            auth_types_enum=[AuthType.EVENT_MATCHES, AuthType.EVENT_INFO],
            description="my write key",
            secret="supersecret",
            event_list=[ndb.Key(Event, "2023test")],
            expiration=expiration,
        )
    ]

    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/api_keys/list", req, ApiKeysResponse)
    assert resp == ApiKeysResponse(
        code=200,
        message="",
        read_keys=[
            ApiReadKeyMessage(
                key="readkey123",
                description="my read key",
                created=created.isoformat(),
            )
        ],
        write_keys=[
            ApiWriteKeyMessage(
                auth_id="writekey456",
                secret="supersecret",
                description="my write key",
                event_keys=["2023test"],
                auth_types=["event matches", "event info"],
                expiration=expiration.isoformat(),
            )
        ],
    )


def test_add_api_read_key_no_auth(
    api_client: Client, mock_clientapi_auth_no_account: None
) -> None:
    req = AddApiReadKeyMessage(description="test")
    resp = make_clientapi_request(api_client, "/api_keys/read/add", req)
    assert resp["code"] == 401


def test_add_api_read_key(api_client: Client, mock_clientapi_auth: User) -> None:
    mock = cast(Mock, mock_clientapi_auth)
    created = datetime.datetime(2023, 1, 2, 3, 4, 5)
    mock.add_api_read_key = Mock(
        return_value=ApiAuthAccess(
            id="newkey123",
            auth_types_enum=[AuthType.READ_API],
            description="my new key",
            created=created,
        )
    )

    req = AddApiReadKeyMessage(description="my new key")
    resp = make_clientapi_request(
        api_client, "/api_keys/read/add", req, AddApiReadKeyResponse
    )
    assert resp["code"] == 200
    assert resp["read_key"] == ApiReadKeyMessage(
        key="newkey123",
        description="my new key",
        created=created.isoformat(),
    )
    mock.add_api_read_key.assert_called_once_with("my new key")


def test_add_api_read_key_empty_description(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    mock = cast(Mock, mock_clientapi_auth)
    mock.add_api_read_key = Mock()

    req = AddApiReadKeyMessage(description="   ")
    resp = make_clientapi_request(api_client, "/api_keys/read/add", req)
    assert resp["code"] == 400
    mock.add_api_read_key.assert_not_called()


def test_delete_api_read_key_no_auth(
    api_client: Client, mock_clientapi_auth_no_account: None
) -> None:
    req = DeleteApiReadKeyMessage(key_id="readkey123")
    resp = make_clientapi_request(api_client, "/api_keys/read/delete", req)
    assert resp["code"] == 401


def test_delete_api_read_key(api_client: Client, mock_clientapi_auth: User) -> None:
    mock = cast(Mock, mock_clientapi_auth)
    api_key = ApiAuthAccess(
        id="readkey123",
        auth_types_enum=[AuthType.READ_API],
        description="my read key",
    )
    mock.api_read_key = Mock(return_value=api_key)
    mock.delete_api_key = Mock()

    req = DeleteApiReadKeyMessage(key_id="readkey123")
    resp = make_clientapi_request(api_client, "/api_keys/read/delete", req)
    assert resp["code"] == 200
    mock.api_read_key.assert_called_once_with("readkey123")
    mock.delete_api_key.assert_called_once_with(api_key)


def test_delete_api_read_key_not_found(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    mock = cast(Mock, mock_clientapi_auth)
    mock.api_read_key = Mock(return_value=None)
    mock.delete_api_key = Mock()

    req = DeleteApiReadKeyMessage(key_id="doesnotexist")
    resp = make_clientapi_request(api_client, "/api_keys/read/delete", req)
    assert resp["code"] == 404
    mock.delete_api_key.assert_not_called()
