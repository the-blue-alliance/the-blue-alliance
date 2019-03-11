import unittest2

from consts.notification_type import NotificationType

from tbans.models.notifications.update_subscriptions import UpdateSubscriptionsNotification


class TestUpdateSubscriptionsNotification(unittest2.TestCase):

    def test_type(self):
        self.assertEquals(UpdateSubscriptionsNotification._type(), NotificationType.UPDATE_SUBSCRIPTION)
