from unittest.mock import ANY, patch

import pytest
from google.appengine.api import urlfetch
from google.appengine.ext import testbed

from backend.common.models.notifications.requests.request import Request
from backend.common.models.notifications.requests.webhook_request import (
    WebhookRequest,
)
from backend.common.models.notifications.tests.mocks.notifications.mock_notification import (
    MockNotification,
)


@pytest.fixture(autouse=True)
def auto_add_urlfetch_stub(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    pass


def test_subclass():
    request = WebhookRequest(
        MockNotification(), "https://www.thebluealliance.com", "secret"
    )
    assert isinstance(request, Request)


def test_str():
    message_str = WebhookRequest(
        MockNotification(), "https://www.thebluealliance.com", "secret"
    )
    assert "WebhookRequest(notification=" in str(message_str)


def test_webhook_message():
    webhook_message_data = {"test": "something"}
    notification = MockNotification(webhook_message_data=webhook_message_data)
    message = WebhookRequest(notification, "https://www.thebluealliance.com", "secret")
    assert (
        message._json_string()
    ), '{"message_data": {"test": "something"}, "message_type": "verification"}'


def test_webhook_message_no_payload():
    notification = MockNotification()
    message = WebhookRequest(notification, "https://www.thebluealliance.com", "secret")
    assert message._json_string(), '{"message_type": "verification"}'


def test_generate_webhook_checksum():
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )
    message_json = message._json_string()
    assert (
        message._generate_webhook_checksum(message_json)
        == "82bb620ceffa9ee31480e60b98f1881251fb68c3"
    )


def test_generate_webhook_checksum_hmac():
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )
    message_json = message._json_string()
    assert (
        message._generate_webhook_hmac(message_json)
        == "a143b493f9a31077f7ff742dc3f59c8d73e6e2c2f09dde5f1a73c33059b77151"
    )


def test_generate_webhook_checksum_hmac_unicode_nonascii():
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "\x80secret",
    )
    message_json = message._json_string()
    assert (
        message._generate_webhook_hmac(message_json)
        == "a986aff362a9d432e100143825508afa3615ecd1b6c59c80b6b4aa201194514a"
    )


@patch("google.appengine.api.urlfetch.fetch")
def test_send_headers(mock_fetch):
    mock_fetch.return_value.status_code = 200

    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-TBA-Version": "1",
        "X-TBA-Checksum": "82bb620ceffa9ee31480e60b98f1881251fb68c3",
        "X-TBA-HMAC": "a143b493f9a31077f7ff742dc3f59c8d73e6e2c2f09dde5f1a73c33059b77151",
    }

    success, valid_url = message.send()

    mock_fetch.assert_called_once_with(
        "https://www.thebluealliance.com",
        payload=ANY,
        method=urlfetch.POST,
        headers=headers,
    )
    assert success
    assert valid_url


@patch("google.appengine.api.urlfetch.fetch")
def test_send(mock_fetch):
    mock_fetch.return_value.status_code = 200

    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    success, valid_url = message.send()

    mock_fetch.assert_called_once()
    assert success
    assert valid_url


@patch("google.appengine.api.urlfetch.fetch")
@pytest.mark.parametrize("code", [400, 401, 500])
def test_send_errors(mock_fetch, code):
    mock_fetch.return_value.status_code = code

    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    success, valid_url = message.send()

    mock_fetch.assert_called_once()
    assert success
    assert not valid_url


@patch("google.appengine.api.urlfetch.fetch")
def test_send_error_unknown(mock_fetch):
    mock_fetch.return_value.status_code = -1

    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    success, valid_url = message.send()

    mock_fetch.assert_called_once()
    assert success
    assert not valid_url


@patch("google.appengine.api.urlfetch.fetch")
def test_send_fail_404(mock_fetch):
    mock_fetch.return_value.status_code = 404

    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    success, valid_url = message.send()

    mock_fetch.assert_called_once()
    assert success
    assert not valid_url


@patch("google.appengine.api.urlfetch.fetch")
def test_send_error_other(mock_fetch):
    mock_fetch.side_effect = urlfetch.Error("testing")

    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    success, valid_url = message.send()

    mock_fetch.assert_called_once()
    assert not success
    assert valid_url
