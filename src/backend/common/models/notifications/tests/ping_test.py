from backend.common.consts.notification_type import NotificationType
from backend.common.models.notifications.ping import PingNotification


def test_type():
    assert PingNotification._type() == NotificationType.PING


def test_notification_payload():
    notification = PingNotification()
    assert notification.fcm_notification is not None
    fcm_notification = notification.fcm_notification
    assert fcm_notification.title == notification._title
    assert fcm_notification.body == notification._body


def test_data_payload():
    notification = PingNotification()
    assert notification.data_payload is None


def test_webhook_message_data():
    notification = PingNotification()
    assert notification.webhook_message_data == {
        "title": notification._title,
        "desc": notification._body,
    }
