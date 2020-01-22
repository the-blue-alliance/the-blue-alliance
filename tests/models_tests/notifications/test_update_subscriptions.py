import unittest2

from consts.notification_type import NotificationType

from models.notifications.update_subscriptions import UpdateSubscriptionsNotification


class TestUpdateSubscriptionsNotification(unittest2.TestCase):

    def setUp(self):
        self.notification = UpdateSubscriptionsNotification('abcd')

    def test_type(self):
        self.assertEqual(UpdateSubscriptionsNotification._type(), NotificationType.UPDATE_SUBSCRIPTIONS)

    def test_platform_config(self):
        self.assertEqual(self.notification.platform_config.collapse_key, 'abcd_update_subscriptions')
