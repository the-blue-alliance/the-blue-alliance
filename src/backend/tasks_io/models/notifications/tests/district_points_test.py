import unittest

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.district import District
from backend.tasks_io.models.notifications import DistrictPointsNotification


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestDistrictPointsNotification(unittest.TestCase):
    def setUp(self):
        district = District(
            id="2015fim",
            year=2015,
            abbreviation="fim",
            display_name="FIRST In Michigan",
        )
        self.notification = DistrictPointsNotification(district)

    def test_type(self):
        assert (
            DistrictPointsNotification._type()
            == NotificationType.DISTRICT_POINTS_UPDATED
        )

    def test_fcm_notification(self):
        assert self.notification.fcm_notification is not None
        assert self.notification.fcm_notification.title == "FIM District Points Updated"
        assert (
            self.notification.fcm_notification.body
            == "FIRST In Michigan district point calculations have been updated."
        )

    def test_data_payload(self):
        assert self.notification.data_payload == {"district_key": "2015fim"}

    def test_webhook_message_data(self):
        assert self.notification.webhook_message_data == {
            "district_key": "2015fim",
            "district_name": "FIRST In Michigan",
        }
