import unittest2

from google.appengine.ext import testbed

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from notifications.update_subscriptions import UpdateSubscriptionsNotification


class TestUpdateSubscriptionsNotification(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        self.test_user = "1124"  # Mock user ID
        self.sending_key = "31415926"
        self.keys = {ClientType.OS_ANDROID: [self.sending_key, "123456", "abcdefg"]}
        self.notification = UpdateSubscriptionsNotification(self.test_user, self.sending_key)
        self.notification.keys = self.keys

    def tearDown(self):
        self.testbed.deactivate()

    def test_build(self):
        expected = {}
        expected['notification_type'] = NotificationType.type_names[NotificationType.UPDATE_SUBSCRIPTIONS]
        data = self.notification._build_dict()

        self.assertEqual(expected, data)

    """
    Because this notification type uses its own render method, we test that implementation here
    We're testing that we have matches on the user list and collapse key (data is tested above)
    """
    def test_render_android(self):
        collapse_key = "{}_subscriptions_update".format(self.test_user)
        user_list = ["123456", "abcdefg"]

        message = self.notification._render_android()
        self.assertEqual(collapse_key, message.collapse_key)
        self.assertEqual(user_list, message.device_tokens)
