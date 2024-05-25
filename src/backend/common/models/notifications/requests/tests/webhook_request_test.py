from unittest.mock import ANY, Mock, patch

import pytest

from backend.common.models.notifications.requests.request import Request
from backend.common.models.notifications.requests.webhook_request import (
    WebhookRequest,
)
from backend.common.models.notifications.tests.mocks.notifications.mock_notification import (
    MockNotification,
)


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


def test_send_headers():
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

    with patch("requests.post") as mock_post:
        message.send()
    mock_post.assert_called_once_with(
        "https://www.thebluealliance.com", data=ANY, headers=headers
    )


def test_send():
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    with patch(
        "requests.post", return_value=Mock(status_code=200)
    ) as mock_post, patch.object(message, "defer_track_notification") as mock_track:
        success = message.send()
    mock_post.assert_called_once()
    mock_track.assert_called_once_with(1)
    assert success


@pytest.mark.parametrize("code", [400, 401, 500])
def test_send_errors(code):
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    with patch(
        "requests.post", return_value=Mock(status_code=code)
    ) as mock_post, patch.object(message, "defer_track_notification") as mock_track:
        success = message.send()
    mock_post.assert_called_once()
    mock_track.assert_not_called()
    assert success


def test_send_error_unknown():
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    with patch(
        "requests.post", return_value=Mock(status_code=-1)
    ) as mock_post, patch.object(message, "defer_track_notification") as mock_track:
        success = message.send()
    mock_post.assert_called_once()
    mock_track.assert_not_called()
    assert success


def test_send_fail_404():
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    with patch(
        "requests.post", return_value=Mock(status_code=404)
    ) as mock_post, patch.object(message, "defer_track_notification") as mock_track:
        success = message.send()
    mock_post.assert_called_once()
    mock_track.assert_not_called()
    assert not success


def test_send_error_other():
    message = WebhookRequest(
        MockNotification(webhook_message_data={"data": "value"}),
        "https://www.thebluealliance.com",
        "secret",
    )

    error_mock = Mock()
    error_mock.side_effect = Exception("testing")

    with patch("requests.post", error_mock) as mock_post, patch.object(
        message, "defer_track_notification"
    ) as mock_track:
        message.send()
    mock_post.assert_called_once()
    mock_track.assert_not_called()
