from unittest.mock import Mock, patch

import pytest
from firebase_admin import messaging

from backend.common.consts.fcm.platform_priority import PlatformPriority
from backend.common.models.fcm.platform_config import PlatformConfig
from backend.common.models.notifications.requests.fcm_request import (
    FCMRequest,
    MAXIMUM_TOKENS,
)
from backend.common.models.notifications.requests.request import Request
from backend.common.models.notifications.tests.mocks.notifications.mock_notification import (
    MockNotification,
)


@pytest.fixture
def fcm_app():
    return Mock()


def test_subclass(fcm_app):
    request = FCMRequest(fcm_app, MockNotification(), tokens=["abcd"])
    assert isinstance(request, Request)


def test_init_app(fcm_app):
    FCMRequest(fcm_app, notification=MockNotification(), tokens=["abcd"])


def test_init_delivery_none(fcm_app):
    with pytest.raises(TypeError):
        FCMRequest(fcm_app, notification=MockNotification())


def test_init_delivery_too_many_tokens(fcm_app):
    with pytest.raises(
        ValueError,
        match=f"FCMRequest tokens must contain less than {MAXIMUM_TOKENS} tokens",
    ):
        FCMRequest(
            fcm_app,
            notification=MockNotification(),
            tokens=["a" for i in range(MAXIMUM_TOKENS + 1)],
        )


def test_str(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    assert "FCMRequest(tokens=['abc'], notification=MockNotification())" == str(request)


def test_send(fcm_app):
    batch_response = messaging.BatchResponse(
        [messaging.SendResponse({"name": "abc"}, None)]
    )
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    with patch.object(
        messaging, "send_each_for_multicast", return_value=batch_response
    ) as mock_send, patch.object(request, "defer_track_notification") as mock_track:
        response = request.send()
    mock_send.assert_called_once()
    mock_track.assert_called_once_with(1)
    assert response == batch_response


def test_send_failed(fcm_app):
    batch_response = messaging.BatchResponse([messaging.SendResponse(None, "a")])
    request = FCMRequest(
        fcm_app, notification=MockNotification(), tokens=["abc", "def"]
    )
    with patch.object(
        messaging, "send_each_for_multicast", return_value=batch_response
    ) as mock_send, patch.object(request, "defer_track_notification") as mock_track:
        response = request.send()
    mock_send.assert_called_once()
    mock_track.assert_not_called()
    assert response == batch_response


def test_send_failed_partial(fcm_app):
    batch_response = messaging.BatchResponse(
        [
            messaging.SendResponse({"name": "abc"}, None),
            messaging.SendResponse(None, "a"),
        ]
    )
    request = FCMRequest(
        fcm_app, notification=MockNotification(), tokens=["abc", "def"]
    )
    with patch.object(
        messaging, "send_each_for_multicast", return_value=batch_response
    ) as mock_send, patch.object(request, "defer_track_notification") as mock_track:
        response = request.send()
    mock_send.assert_called_once()
    mock_track.assert_called_once_with(1)
    assert response == batch_response


def test_fcm_message_empty(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    message = request._fcm_message()
    assert message is not None
    assert message.data is not None
    assert message.notification is None
    assert message.android is None
    assert isinstance(message.apns, messaging.APNSConfig)
    assert message.webpush is None
    assert message.tokens == ["abc"]


def test_fcm_message_apns_sound(fcm_app):
    request = FCMRequest(
        fcm_app,
        notification=MockNotification(
            fcm_notification=messaging.Notification(
                title="Title", body="Some body message"
            )
        ),
        tokens=["abc"],
    )
    message = request._fcm_message()
    assert message is not None
    assert message.data is not None
    assert isinstance(message.notification, messaging.Notification)
    assert message.android is None
    assert isinstance(message.apns, messaging.APNSConfig)
    assert isinstance(message.apns.payload, messaging.APNSPayload)
    assert isinstance(message.apns.payload.aps, messaging.Aps)
    assert message.apns.payload.aps.sound is not None
    assert not message.apns.payload.aps.content_available
    assert message.webpush is None
    assert message.tokens == ["abc"]


def test_fcm_message_apns_content_available(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    message = request._fcm_message()
    assert message is not None
    assert message.data is not None
    assert message.notification is None
    assert message.android is None
    assert isinstance(message.apns, messaging.APNSConfig)
    assert isinstance(message.apns.payload, messaging.APNSPayload)
    assert isinstance(message.apns.payload.aps, messaging.Aps)
    assert message.apns.payload.aps.sound is None
    assert message.apns.payload.aps.content_available
    assert message.webpush is None
    assert message.tokens == ["abc"]


def test_fcm_message_platform_config(fcm_app):
    platform_config = PlatformConfig(
        priority=PlatformPriority.HIGH, collapse_key="collapse_key"
    )
    request = FCMRequest(
        fcm_app,
        notification=MockNotification(platform_config=platform_config),
        tokens=["abc"],
    )
    message = request._fcm_message()
    assert message is not None
    assert message.data is not None
    assert message.notification is None
    assert isinstance(message.android, messaging.AndroidConfig)
    assert isinstance(message.apns, messaging.APNSConfig)
    assert isinstance(message.webpush, messaging.WebpushConfig)
    assert message.tokens == ["abc"]


def test_fcm_message_platform_config_override(fcm_app):
    platform_config = PlatformConfig(
        priority=PlatformPriority.HIGH, collapse_key="collapse_key"
    )
    apns_config = messaging.APNSConfig(headers={"apns-collapse-id": "ios_collapse_key"})
    request = FCMRequest(
        fcm_app,
        notification=MockNotification(
            platform_config=platform_config, apns_config=apns_config
        ),
        tokens=["abc"],
    )
    message = request._fcm_message()
    assert message is not None
    assert message.data is not None
    assert message.notification is None
    assert isinstance(message.android, messaging.AndroidConfig)
    assert isinstance(message.apns, messaging.APNSConfig)
    assert message.apns.headers == {"apns-collapse-id": "ios_collapse_key"}
    assert isinstance(message.webpush, messaging.WebpushConfig)
    assert message.webpush.headers == {"Topic": "collapse_key", "Urgency": "high"}
    assert message.tokens == ["abc"]


def test_fcm_message_data_payload_default(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    message = request._fcm_message()
    assert message is not None
    assert message.data == {"notification_type": "verification"}
    assert message.notification is None
    assert message.android is None
    assert isinstance(message.apns, messaging.APNSConfig)
    assert message.webpush is None
    assert message.tokens == ["abc"]


def test_fcm_message_data_payload(fcm_app):
    request = FCMRequest(
        fcm_app,
        notification=MockNotification(data_payload={"some_data": "some test data"}),
        tokens=["abc"],
    )
    message = request._fcm_message()
    assert message is not None
    assert message.data == {
        "notification_type": "verification",
        "some_data": "some test data",
    }
    assert message.notification is None
    assert message.android is None
    assert isinstance(message.apns, messaging.APNSConfig)
    assert message.webpush is None
    assert message.tokens == ["abc"]


def test_fcm_message_data_payload_none(fcm_app):
    request = FCMRequest(
        fcm_app,
        notification=MockNotification(
            data_payload={"some_data": "some test data", "some_none": None}
        ),
        tokens=["abc"],
    )
    message = request._fcm_message()
    assert message is not None
    assert message.data == {
        "notification_type": "verification",
        "some_data": "some test data",
    }
    assert message.notification is None
    assert message.android is None
    assert isinstance(message.apns, messaging.APNSConfig)
    assert message.webpush is None
    assert message.tokens == ["abc"]


def test_fcm_message_notification(fcm_app):
    request = FCMRequest(
        fcm_app,
        notification=MockNotification(
            fcm_notification=messaging.Notification(
                title="Title", body="Some body message"
            )
        ),
        tokens=["abc"],
    )
    message = request._fcm_message()
    assert message is not None
    assert message.data is not None
    assert isinstance(message.notification, messaging.Notification)
    assert message.android is None
    assert isinstance(message.apns, messaging.APNSConfig)
    assert message.webpush is None
    assert message.tokens == ["abc"]
