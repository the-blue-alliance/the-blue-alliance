from backend.common.consts.notification_type import NotificationType
from backend.common.models.notifications.verification import (
    VerificationNotification,
)


def test_str():
    notification = VerificationNotification("https://thebluealliance.com/", "password")
    assert "{'verification_key': " in str(notification)


def test_type():
    assert VerificationNotification._type() == NotificationType.VERIFICATION


def test_data_payload():
    notification = VerificationNotification("https://thebluealliance.com/", "password")
    assert notification.data_payload is None


def test_webhook_message_data():
    notification = VerificationNotification("https://thebluealliance.com/", "password")
    assert notification.webhook_message_data is not None
    verification_key = notification.webhook_message_data.get("verification_key", None)
    assert verification_key is not None
