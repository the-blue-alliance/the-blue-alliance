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
    with pytest.raises(
        ValueError, match="FCMRequest must contain at least one token or fid"
    ):
        FCMRequest(fcm_app, notification=MockNotification())


def test_init_delivery_empty_lists(fcm_app):
    with pytest.raises(
        ValueError, match="FCMRequest must contain at least one token or fid"
    ):
        FCMRequest(fcm_app, notification=MockNotification(), tokens=[], fids=[])


def test_init_fids(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), fids=["abcd"])
    assert request.fids == ["abcd"]
    assert request.tokens == []


def test_init_delivery_too_many_tokens(fcm_app):
    with pytest.raises(
        ValueError,
        match=f"FCMRequest must contain less than {MAXIMUM_TOKENS} tokens/fids",
    ):
        FCMRequest(
            fcm_app,
            notification=MockNotification(),
            tokens=["a" for i in range(MAXIMUM_TOKENS + 1)],
        )


def test_init_delivery_too_many_fids(fcm_app):
    with pytest.raises(
        ValueError,
        match=f"FCMRequest must contain less than {MAXIMUM_TOKENS} tokens/fids",
    ):
        FCMRequest(
            fcm_app,
            notification=MockNotification(),
            fids=["a" for i in range(MAXIMUM_TOKENS + 1)],
        )


def test_init_delivery_too_many_combined(fcm_app):
    """The SDK caps `len(tokens) + len(fids)` at 500, not each individually"""
    with pytest.raises(
        ValueError,
        match=f"FCMRequest must contain less than {MAXIMUM_TOKENS} tokens/fids",
    ):
        FCMRequest(
            fcm_app,
            notification=MockNotification(),
            tokens=["a" for i in range(MAXIMUM_TOKENS)],
            fids=["b"],
        )


def test_init_delivery_at_combined_limit(fcm_app):
    request = FCMRequest(
        fcm_app,
        notification=MockNotification(),
        tokens=["a" for i in range(MAXIMUM_TOKENS - 1)],
        fids=["b"],
    )
    assert len(request.tokens) + len(request.fids) == MAXIMUM_TOKENS


def test_str(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    assert (
        "FCMRequest(tokens=['abc'], fids=[], notification=MockNotification())"
        == str(request)
    )


def test_str_fids(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), fids=["abc"])
    assert (
        "FCMRequest(tokens=[], fids=['abc'], notification=MockNotification())"
        == str(request)
    )


def test_fcm_message_tokens_only(fcm_app):
    """`tokens` is deprecated in firebase-admin 7.5.0 and `pytest.ini` sets
    `filterwarnings = error`, so this asserts the scoped suppression works."""
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    message = request._fcm_message()
    assert message.tokens == ["abc"]
    assert message.fids is None


def test_fcm_message_fids_only(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), fids=["abc"])
    message = request._fcm_message()
    assert message.tokens is None
    assert message.fids == ["abc"]


def _wire_messages(request: FCMRequest) -> list[dict]:
    # Encode the way `send_each_for_multicast` does. Asserting on
    # `MulticastMessage` attributes alone missed #10786, where tokens were
    # passed as `fids=` and FCM received them as installation IDs.
    return [
        messaging._MessagingService.encode_message(m)
        for m in messaging._get_messages_from_multicast(request._fcm_message())
    ]


def test_fcm_message_tokens_encode_as_token(fcm_app):
    request = FCMRequest(
        fcm_app, notification=MockNotification(), tokens=["abc", "def"]
    )
    wire = _wire_messages(request)
    assert [m.get("token") for m in wire] == ["abc", "def"]
    assert all("fid" not in m for m in wire)


def test_fcm_message_fids_encode_as_fid(fcm_app):
    request = FCMRequest(fcm_app, notification=MockNotification(), fids=["abc", "def"])
    wire = _wire_messages(request)
    assert [m.get("fid") for m in wire] == ["abc", "def"]
    assert all("token" not in m for m in wire)


def test_send(fcm_app):
    batch_response = messaging.BatchResponse(
        [messaging.SendResponse({"name": "abc"}, None)]
    )
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    with (
        patch.object(
            messaging, "send_each_for_multicast", return_value=batch_response
        ) as mock_send,
        patch.object(request, "defer_track_notification") as mock_track,
    ):
        response = request.send()
    mock_send.assert_called_once()
    mock_track.assert_called_once_with(1)
    assert response == batch_response


def test_send_failed(fcm_app):
    batch_response = messaging.BatchResponse([messaging.SendResponse(None, "a")])
    request = FCMRequest(
        fcm_app, notification=MockNotification(), tokens=["abc", "def"]
    )
    with (
        patch.object(
            messaging, "send_each_for_multicast", return_value=batch_response
        ) as mock_send,
        patch.object(request, "defer_track_notification") as mock_track,
    ):
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
    with (
        patch.object(
            messaging, "send_each_for_multicast", return_value=batch_response
        ) as mock_send,
        patch.object(request, "defer_track_notification") as mock_track,
    ):
        response = request.send()
    mock_send.assert_called_once()
    mock_track.assert_called_once_with(1)
    assert response == batch_response


def test_send_track_notification_failure(fcm_app):
    """Analytics tracking failure must not prevent the batch response from being returned.

    The caller (_send_fcm) inspects the batch response to clean up stale
    mobile clients.  If defer_track_notification raises, the response must
    still be returned so that error-handling logic can execute.
    """
    batch_response = messaging.BatchResponse(
        [messaging.SendResponse({"name": "abc"}, None)]
    )
    request = FCMRequest(fcm_app, notification=MockNotification(), tokens=["abc"])
    with (
        patch.object(
            messaging, "send_each_for_multicast", return_value=batch_response
        ) as mock_send,
        patch.object(
            request,
            "defer_track_notification",
            side_effect=Exception("task queue error"),
        ) as mock_track,
    ):
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


def _client(messaging_id, is_fid=False):
    from backend.common.consts.client_type import ClientType
    from backend.common.consts.messaging_id_type import MessagingIdType
    from backend.common.models.mobile_client import MobileClient

    return MobileClient(
        user_id="user_id",
        messaging_id=messaging_id,
        client_type=ClientType.OS_IOS,
        messaging_id_type=(MessagingIdType.FID if is_fid else MessagingIdType.TOKEN),
    )


def test_for_clients_tokens(fcm_app):
    request = FCMRequest.for_clients(
        fcm_app, MockNotification(), [_client("a"), _client("b")]
    )
    assert request.tokens == ["a", "b"]
    assert request.fids == []


def test_for_clients_fids(fcm_app):
    request = FCMRequest.for_clients(
        fcm_app,
        MockNotification(),
        [_client("a", is_fid=True), _client("b", is_fid=True)],
    )
    assert request.fids == ["a", "b"]
    assert request.tokens == []
