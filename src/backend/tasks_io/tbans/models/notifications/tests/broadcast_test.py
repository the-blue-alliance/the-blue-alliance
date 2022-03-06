import unittest

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.tasks_io.tbans.models.notifications.broadcast import BroadcastNotification


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestBroadcastNotification(unittest.TestCase):
    def setUp(self):
        self.notification = BroadcastNotification(
            "Title Here", "Some body message ya dig"
        )

    def test_type(self):
        assert BroadcastNotification._type() == NotificationType.BROADCAST

    def test_fcm_notification(self):
        assert self.notification.fcm_notification is not None
        assert self.notification.fcm_notification.title == "Title Here"
        assert self.notification.fcm_notification.body == "Some body message ya dig"

    def test_data_payload(self):
        assert self.notification.data_payload == {}

    def test_data_payload_url(self):
        notification = BroadcastNotification("T", "B", "https://thebluealliance.com/")
        assert notification.data_payload == {"url": "https://thebluealliance.com/"}

    def test_data_payload_app_version(self):
        notification = BroadcastNotification(
            "T", "B", "https://thebluealliance.com/", "1.0.0"
        )
        assert notification.data_payload == {
            "url": "https://thebluealliance.com/",
            "app_version": "1.0.0",
        }

    def test_data_payload_url_app_version(self):
        notification = BroadcastNotification("T", "B", None, "1.0.0")
        assert notification.data_payload == {"app_version": "1.0.0"}

    def test_webhook_message_data(self):
        payload = {"title": "Title Here", "desc": "Some body message ya dig"}
        assert self.notification.webhook_message_data == payload

    def test_webhook_message_data_url(self):
        notification = BroadcastNotification(
            "T", "B", "https://thebluealliance.com/", None
        )
        payload = {"title": "T", "desc": "B", "url": "https://thebluealliance.com/"}
        assert notification.webhook_message_data == payload

    def test_webhook_message_data_app_version(self):
        notification = BroadcastNotification("T", "B", None, "1.0.0")
        payload = {"title": "T", "desc": "B"}
        assert notification.webhook_message_data == payload

    def test_webhook_message_data_url_app_version(self):
        notification = BroadcastNotification(
            "T", "B", "https://thebluealliance.com/", "1.0.0"
        )
        payload = {"title": "T", "desc": "B", "url": "https://thebluealliance.com/"}
        assert notification.webhook_message_data, payload
