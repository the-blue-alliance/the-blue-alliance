import unittest2

from consts.notification_type import NotificationType

from models.notifications.update_favorites import UpdateFavoritesNotification


class TestUpdateFavoritesNotification(unittest2.TestCase):

    def setUp(self):
        self.notification = UpdateFavoritesNotification('abcd')

    def test_type(self):
        self.assertEqual(UpdateFavoritesNotification._type(), NotificationType.UPDATE_FAVORITES)

    def test_platform_config(self):
        self.assertEqual(self.notification.platform_config.collapse_key, 'abcd_favorite_update')
