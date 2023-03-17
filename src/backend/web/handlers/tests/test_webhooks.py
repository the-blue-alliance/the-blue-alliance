from unittest.mock import patch

from werkzeug.test import Client

from backend.common.consts.client_type import ClientType
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.mobile_client import MobileClient
from backend.common.models.user import User


def test_add_webhook(login_user: User, web_client: Client):
    response = web_client.post(
        "/webhooks/add",
        data={"url": "https://example.com/webhook", "name": "Test Webhook"},
        follow_redirects=True,
    )

    client = MobileClient.query(
        MobileClient.messaging_id == "https://example.com/webhook",
        MobileClient.display_name == "Test Webhook",
    ).get()

    assert response.status_code == 200
    assert client is not None


def test_add_webhook_already_exists(login_user: User, web_client: Client):
    client = MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.uid),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        verification_code="abc",
        verified=False,
    )
    client_key = client.put()

    response = web_client.post(
        "/webhooks/add",
        data={"url": "https://example.com/webhook", "name": "Test Webhook"},
        follow_redirects=True,
    )

    # Check that the existing webhook is updated
    assert response.status_code == 200
    assert MobileClient.query().count() == 1

    updated_webhook = client_key.get()
    assert updated_webhook.verified is False
    assert updated_webhook.secret != client.secret


def test_add_webhook_incomplete_form(
    login_user: User, web_client: Client, captured_templates
):
    # Missing field for URL
    web_client.post(
        "/webhooks/add",
        data={"name": "Test Webhook"},
        follow_redirects=True,
    )

    template, context = captured_templates[0]
    assert template.name == "webhook_add.html"
    assert context["error"] is not None


def test_delete_webhook(login_user: User, web_client: Client):
    client = MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.uid),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
    )
    client.put()

    response = web_client.post(
        "/webhooks/delete",
        data={"client_id": client.key.id()},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert MobileClient.query().count() == 0


def test_verify_webhook(login_user: User, web_client: Client):
    client = MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.uid),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        verification_code="abc",
        verified=False,
    )
    client_key = client.put()

    response = web_client.post(
        f"/webhooks/verify/{client.key.id()}",
        data={"code": "abc"},
        follow_redirects=True,
    )

    updated_webhook = client_key.get()

    assert response.status_code == 200
    assert updated_webhook.verified is True


def test_verify_webhook_wrong_code(
    login_user: User, web_client: Client, captured_templates
):
    client = MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.uid),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        verification_code="abc",
        verified=False,
    )
    client_key = client.put()

    web_client.post(
        f"/webhooks/verify/{client.key.id()}",
        data={"code": "xyz"},
        follow_redirects=True,
    )

    updated_webhook = client_key.get()
    template, context = captured_templates[0]

    assert updated_webhook.verified is False
    assert template.name == "webhook_verify.html"
    assert context["error"] is not None


def test_verify_webhook_empty_code(
    login_user: User, web_client: Client, captured_templates
):
    client = MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.uid),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        verification_code="abc",
        verified=False,
    )
    client_key = client.put()

    # Missing verification code in POST data
    web_client.post(
        f"/webhooks/verify/{client.key.id()}",
        follow_redirects=True,
    )

    updated_webhook = client_key.get()
    template, context = captured_templates[0]

    assert updated_webhook.verified is False
    assert template.name == "webhook_verify.html"
    assert context["error"] is not None


def test_send_verification(login_user: User, web_client: Client):
    client = MobileClient(
        parent=login_user.account_key,
        user_id=str(login_user.uid),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        verification_code="abc",
        verified=True,
    )
    client_key = client.put()

    with patch.object(TBANSHelper, "verify_webhook") as mock_verify_webhook:
        mock_verify_webhook.return_value = "xyz"

        response = web_client.post(
            "/webhooks/send_verification",
            data={"client_id": client.key.id()},
            follow_redirects=True,
        )

    updated_webhook = client_key.get()

    assert response.status_code == 200
    assert updated_webhook.verified is False
    assert updated_webhook.verification_code == "xyz"


def test_send_verification_different_user(login_user: User, web_client: Client):
    # Webhook is not owned by the login_user
    different_user = User(
        session_claims={"uid": "123", "email": "user@thebluealliance.com"}
    )
    client = MobileClient(
        parent=different_user.account_key,
        user_id=different_user.uid,
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        verification_code="abc",
        verified=False,
    )
    client_key = client.put()

    with patch.object(TBANSHelper, "verify_webhook") as mock_verify_webhook:
        web_client.post(
            "/webhooks/send_verification",
            data={"client_id": client.key.id()},
            follow_redirects=True,
        )
        assert not mock_verify_webhook.called

    updated_webhook = client_key.get()
    assert updated_webhook.verified is False
    assert updated_webhook.verification_code == "abc"
