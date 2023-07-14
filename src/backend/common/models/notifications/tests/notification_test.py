import pytest
from firebase_admin import messaging

from backend.common.consts.fcm.platform_priority import PlatformPriority
from backend.common.models.fcm.platform_config import PlatformConfig
from backend.common.models.mobile_client import MobileClient
from backend.common.models.notifications.notification import Notification
from backend.common.models.notifications.tests.mocks.notifications.mock_notification import (
    MockNotification,
)


def test_str():
    fcm_notification = messaging.Notification(title="Title Here", body="Body here")
    data_payload = {"data": "payload"}
    platform_config = PlatformConfig(
        priority=PlatformPriority.HIGH, collapse_key="general_collapse_key"
    )
    apns_config = messaging.APNSConfig(headers={"apns-collapse-id": "ios_collapse_key"})

    notification = MockNotification(
        fcm_notification=fcm_notification,
        data_payload=data_payload,
        platform_config=platform_config,
        apns_config=apns_config,
    )
    assert (
        str(notification)
        == "MockNotification(data_payload={'data': 'payload'} fcm_notification.title=\"Title Here\" fcm_notification.body=\"Body here\" platform_config=PlatformConfig(collapse_key=\"general_collapse_key\" priority=1) apns_config={'apns-collapse-id': 'ios_collapse_key'} webhook_message_data={'data': 'payload'})"
    )


def test_default_filter() -> None:
    notification = Notification()
    client = MobileClient()
    assert notification.should_send_to_client(client) is True


def test_type_raises():
    with pytest.raises(NotImplementedError):
        Notification._type()


def test_webhook_message_data_same_data_payload():
    data_payload = {"data": "here"}
    notification = MockNotification(data_payload=data_payload)
    assert notification.data_payload == data_payload
    assert notification.webhook_message_data == data_payload


def test_webhook_message_data():
    webhook_message_data = {"data": "here"}
    notification = MockNotification(webhook_message_data=webhook_message_data)
    assert notification.data_payload is None
    assert notification.webhook_message_data == webhook_message_data
