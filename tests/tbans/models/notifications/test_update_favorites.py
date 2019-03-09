import unittest2

from consts.notification_type import NotificationType

from tbans.models.notifications.update_favorites import UpdateFavoritesNotification


class TestUpdateFavoritesNotification(unittest2.TestCase):

    def test_type(self):
        self.assertEquals(UpdateFavoritesNotification._type(), NotificationType.UPDATE_FAVORITES)
