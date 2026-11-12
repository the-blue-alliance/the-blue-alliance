from typing import Any, Iterator
from unittest.mock import Mock, patch

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.client_api_types import (
    AddWebhookResponse,
    ListWebhooksResponse,
    WebhookMessage,
)
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.consts.client_type import ClientType
from backend.common.consts.notification_type import NotificationType
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.account import Account
from backend.common.models.mobile_client import MobileClient
from backend.common.models.user import User


def make_webhook(
    account_key: ndb.Key | None,
    url: str = "https://example.com/hook",
    verified: bool = False,
    client_type: ClientType = ClientType.WEBHOOK,
) -> MobileClient:
    webhook = MobileClient(
        parent=account_key,
        user_id=str(none_throws(account_key).id()),
        messaging_id=url,
        display_name="My Hook",
        secret="oldsecret",
        client_type=client_type,
        verified=verified,
        verification_code="goodcode",
    )
    webhook.put()
    return webhook


def webhook_id(webhook: MobileClient) -> str:
    return str(webhook.key.id())


@pytest.fixture
def mock_verify_webhook() -> Iterator[Mock]:
    with patch.object(
        TBANSHelper, "verify_webhook", return_value="newcode"
    ) as mock_verify:
        yield mock_verify


@pytest.mark.parametrize(
    "endpoint, req",
    [
        ("/webhooks/list", {}),
        ("/webhooks/add", {"name": "Hook", "url": "https://example.com"}),
        ("/webhooks/verify", {"webhook_id": "1", "code": "abc"}),
        ("/webhooks/send_verification", {"webhook_id": "1"}),
        ("/webhooks/delete", {"webhook_id": "1"}),
        (
            "/webhooks/test",
            {"webhook_id": "1", "notification_type": "upcoming_match"},
        ),
    ],
)
def test_webhook_endpoint_requires_sign_in(
    api_client: Client,
    mock_clientapi_auth_no_account: None,
    endpoint: str,
    req: dict[str, Any],
) -> None:
    resp = make_clientapi_request(api_client, endpoint, req)
    assert resp["code"] == 401


def test_list_webhooks_returns_the_users_webhooks(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key, verified=True)

    resp = make_clientapi_request(
        api_client, "/webhooks/list", {}, ListWebhooksResponse
    )

    assert resp["webhooks"] == [
        WebhookMessage(
            webhook_id=webhook_id(webhook),
            name="My Hook",
            url="https://example.com/hook",
            secret="oldsecret",
            verified=True,
        )
    ]


def test_list_webhooks_leaves_out_phones(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    make_webhook(
        mock_clientapi_auth.account_key, url="fcmtoken", client_type=ClientType.OS_IOS
    )

    resp = make_clientapi_request(
        api_client, "/webhooks/list", {}, ListWebhooksResponse
    )

    assert resp["webhooks"] == []


def test_list_webhooks_leaves_out_other_accounts_webhooks(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    make_webhook(Account(email="other@tba.com").put())

    resp = make_clientapi_request(
        api_client, "/webhooks/list", {}, ListWebhooksResponse
    )

    assert resp["webhooks"] == []


def test_add_webhook_saves_an_unverified_webhook(
    api_client: Client, mock_clientapi_auth: User, mock_verify_webhook: Mock
) -> None:
    make_clientapi_request(
        api_client,
        "/webhooks/add",
        {"name": "Hook", "url": "https://example.com/new"},
    )

    webhook = MobileClient.query(ancestor=mock_clientapi_auth.account_key).get()
    assert (webhook.client_type, webhook.verified, webhook.verification_code) == (
        ClientType.WEBHOOK,
        False,
        "newcode",
    )


def test_add_webhook_sends_a_verification_to_the_url(
    api_client: Client, mock_clientapi_auth: User, mock_verify_webhook: Mock
) -> None:
    resp = make_clientapi_request(
        api_client,
        "/webhooks/add",
        {"name": "Hook", "url": "https://example.com/new"},
        AddWebhookResponse,
    )

    mock_verify_webhook.assert_called_once_with(
        "https://example.com/new", resp["webhook"]["secret"]
    )


def test_add_webhook_returns_the_new_webhook(
    api_client: Client, mock_clientapi_auth: User, mock_verify_webhook: Mock
) -> None:
    resp = make_clientapi_request(
        api_client,
        "/webhooks/add",
        {"name": "Hook", "url": "https://example.com/new"},
        AddWebhookResponse,
    )

    webhook = resp["webhook"]
    assert (webhook["name"], webhook["url"], webhook["verified"]) == (
        "Hook",
        "https://example.com/new",
        False,
    )


def test_add_webhook_with_an_existing_url_replaces_its_secret(
    api_client: Client, mock_clientapi_auth: User, mock_verify_webhook: Mock
) -> None:
    make_webhook(mock_clientapi_auth.account_key, verified=True)

    make_clientapi_request(
        api_client,
        "/webhooks/add",
        {"name": "Hook", "url": "https://example.com/hook"},
    )

    webhooks = MobileClient.query(ancestor=mock_clientapi_auth.account_key).fetch()
    assert [(w.secret != "oldsecret", w.verified) for w in webhooks] == [(True, False)]


@pytest.mark.parametrize(
    "name, url",
    [("", "https://example.com/hook"), ("Hook", ""), ("  ", "  ")],
)
def test_add_webhook_rejects_a_blank_name_or_url(
    api_client: Client,
    mock_clientapi_auth: User,
    mock_verify_webhook: Mock,
    name: str,
    url: str,
) -> None:
    resp = make_clientapi_request(
        api_client, "/webhooks/add", {"name": name, "url": url}
    )
    assert resp["code"] == 400


def test_verify_webhook_with_the_right_code_marks_it_verified(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key)

    make_clientapi_request(
        api_client,
        "/webhooks/verify",
        {"webhook_id": webhook_id(webhook), "code": "goodcode"},
    )

    assert webhook.key.get().verified is True


def test_verify_webhook_with_a_wrong_code_returns_400(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key)

    resp = make_clientapi_request(
        api_client,
        "/webhooks/verify",
        {"webhook_id": webhook_id(webhook), "code": "badcode"},
    )

    assert resp["code"] == 400


def test_verify_webhook_with_a_wrong_code_leaves_it_unverified(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key)

    make_clientapi_request(
        api_client,
        "/webhooks/verify",
        {"webhook_id": webhook_id(webhook), "code": "badcode"},
    )

    assert webhook.key.get().verified is False


def test_verify_webhook_of_another_account_returns_404(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(Account(email="other@tba.com").put())

    resp = make_clientapi_request(
        api_client,
        "/webhooks/verify",
        {"webhook_id": webhook_id(webhook), "code": "goodcode"},
    )

    assert resp["code"] == 404


@pytest.mark.parametrize("bad_id", ["", "abc", "-1", "999"])
def test_verify_webhook_with_an_unknown_id_returns_404(
    api_client: Client, mock_clientapi_auth: User, bad_id: str
) -> None:
    resp = make_clientapi_request(
        api_client, "/webhooks/verify", {"webhook_id": bad_id, "code": "goodcode"}
    )
    assert resp["code"] == 404


def test_send_verification_stores_the_new_code(
    api_client: Client, mock_clientapi_auth: User, mock_verify_webhook: Mock
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key)

    make_clientapi_request(
        api_client,
        "/webhooks/send_verification",
        {"webhook_id": webhook_id(webhook)},
    )

    assert webhook.key.get().verification_code == "newcode"


def test_send_verification_marks_the_webhook_unverified(
    api_client: Client, mock_clientapi_auth: User, mock_verify_webhook: Mock
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key, verified=True)

    make_clientapi_request(
        api_client,
        "/webhooks/send_verification",
        {"webhook_id": webhook_id(webhook)},
    )

    assert webhook.key.get().verified is False


def test_send_verification_uses_the_existing_secret(
    api_client: Client, mock_clientapi_auth: User, mock_verify_webhook: Mock
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key)

    make_clientapi_request(
        api_client,
        "/webhooks/send_verification",
        {"webhook_id": webhook_id(webhook)},
    )

    mock_verify_webhook.assert_called_once_with("https://example.com/hook", "oldsecret")


def test_delete_webhook_removes_it(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key)

    make_clientapi_request(
        api_client, "/webhooks/delete", {"webhook_id": webhook_id(webhook)}
    )

    assert webhook.key.get() is None


def test_delete_webhook_does_not_delete_a_phone(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    phone = make_webhook(
        mock_clientapi_auth.account_key, url="fcmtoken", client_type=ClientType.OS_IOS
    )

    resp = make_clientapi_request(
        api_client, "/webhooks/delete", {"webhook_id": webhook_id(phone)}
    )

    assert resp["code"] == 404


def test_send_webhook_test_sends_the_notification(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key, verified=True)

    with patch.object(TBANSHelper, "send_webhook_test", return_value=True) as mock_send:
        make_clientapi_request(
            api_client,
            "/webhooks/test",
            {
                "webhook_id": webhook_id(webhook),
                "notification_type": "upcoming_match",
                "match_key": "2014necmp_f1m1",
            },
        )

    mock_send.assert_called_once_with(
        webhook,
        NotificationType.UPCOMING_MATCH,
        event_key=None,
        match_key="2014necmp_f1m1",
        district_key=None,
    )


def test_send_webhook_test_returns_400_when_sending_fails(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key, verified=True)

    with patch.object(TBANSHelper, "send_webhook_test", return_value=False):
        resp = make_clientapi_request(
            api_client,
            "/webhooks/test",
            {"webhook_id": webhook_id(webhook), "notification_type": "match_score"},
        )

    assert resp["code"] == 400


def test_send_webhook_test_to_an_unverified_webhook_returns_400(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key)

    resp = make_clientapi_request(
        api_client,
        "/webhooks/test",
        {"webhook_id": webhook_id(webhook), "notification_type": "match_score"},
    )

    assert resp["code"] == 400


def test_send_webhook_test_with_an_unknown_type_returns_400(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    webhook = make_webhook(mock_clientapi_auth.account_key, verified=True)

    resp = make_clientapi_request(
        api_client,
        "/webhooks/test",
        {"webhook_id": webhook_id(webhook), "notification_type": "not_a_type"},
    )

    assert resp["code"] == 400
