import unittest2

from consts.notification_type import NotificationType

from models.district import District
from models.notifications.district_points import DistrictPointsNotification


class TestDistrictPointsNotification(unittest2.TestCase):

    def setUp(self):
        district = District(id='2015fim', year=2015, abbreviation='fim', display_name='FIRST In Michigan')
        self.notification = DistrictPointsNotification(district)

    def test_type(self):
        self.assertEqual(DistrictPointsNotification._type(), NotificationType.DISTRICT_POINTS_UPDATED)

    def test_fcm_notification(self):
        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'FIM District Points Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'FIRST In Michigan district point calculations have been updated.')

    def test_data_payload(self):
        self.assertEqual(self.notification.data_payload, {'district_key': '2015fim'})

    def test_webhook_message_data(self):
        self.assertEqual(self.notification.webhook_message_data, {'district_key': '2015fim', 'district_name': 'FIRST In Michigan'})
