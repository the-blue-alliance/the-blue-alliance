from mock import patch
import unittest2

from consts.model_type import ModelType
from consts.notification_type import NotificationType

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.mytba_helper import MyTBAHelper
from helpers.notification_helper import NotificationHelper

from models.account import Account
from models.favorite import Favorite
from models.subscription import Subscription


class TestMyBAHelper(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_add_favorite_200(self):
        favorite = Favorite(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        # Favorite does not already exist - return a 200 and put
        with patch.object(NotificationHelper, 'send_favorite_update') as mock_send_favorite_update, \
             patch.object(favorite, 'put') as mock_put:
                self.assertEqual(MyTBAHelper.add_favorite(favorite), 200)
                mock_put.assert_called_once()
                mock_send_favorite_update.assert_called_once_with('user_id', '')

    def test_add_favorite_200_sending_device_key(self):
        favorite = Favorite(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        # Favorite does not already exist - return a 200 and put
        with patch.object(NotificationHelper, 'send_favorite_update') as mock_send_favorite_update, \
             patch.object(favorite, 'put') as mock_put:
                self.assertEqual(MyTBAHelper.add_favorite(favorite, 'sending_device_key'), 200)
                mock_put.assert_called_once()
                mock_send_favorite_update.assert_called_once_with('user_id', 'sending_device_key')

    def test_add_favorite_304(self):
        favorite = Favorite(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        favorite.put()
        # Favorite already exists - return a 304
        with patch.object(NotificationHelper, 'send_favorite_update') as mock_send_favorite_update:
            self.assertEqual(MyTBAHelper.add_favorite(favorite), 304)
            mock_send_favorite_update.assert_not_called()

    def test_remove_favorite_404(self):
        # Favorite does not exist - 404
        with patch.object(NotificationHelper, 'send_favorite_update') as mock_send_favorite_update:
            self.assertEqual(MyTBAHelper.remove_favorite('user_id', 'model_key', ModelType.TEAM), 404)
            mock_send_favorite_update.assert_not_called()

    def test_remove_favorite_200(self):
        favorite = Favorite(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        favorite_key = favorite.put()
        # Favorite does not exist - 404
        with patch.object(NotificationHelper, 'send_favorite_update') as mock_send_favorite_update, \
             patch.object(ndb, 'delete_multi') as mock_delete:
                self.assertEqual(MyTBAHelper.remove_favorite(favorite.user_id, favorite.model_key, favorite.model_type), 200)
                mock_delete.assert_called_once_with([favorite_key])
                mock_send_favorite_update.assert_called_once_with('user_id', '')

    def test_remove_favorite_200_sending_device_key(self):
        favorite = Favorite(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        favorite_key = favorite.put()
        # Favorite does not exist - 404
        with patch.object(NotificationHelper, 'send_favorite_update') as mock_send_favorite_update, \
             patch.object(ndb, 'delete_multi') as mock_delete:
                self.assertEqual(MyTBAHelper.remove_favorite(favorite.user_id, favorite.model_key, favorite.model_type, 'sending_device_key'), 200)
                mock_delete.assert_called_once_with([favorite_key])
                mock_send_favorite_update.assert_called_once_with('user_id', 'sending_device_key')

    def test_add_subscription_200(self):
        subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        # Subscription does not already exist - return a 200 and put
        with patch.object(NotificationHelper, 'send_subscription_update') as mock_send_subscription_update, \
             patch.object(subscription, 'put') as mock_put:
                self.assertEqual(MyTBAHelper.add_subscription(subscription), 200)
                mock_put.assert_called_once()
                mock_send_subscription_update.assert_called_once_with('user_id', '')

    def test_add_subscription_200_sending_device_key(self):
        subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        # Subscription does not already exist - return a 200 and put
        with patch.object(NotificationHelper, 'send_subscription_update') as mock_send_subscription_update, \
             patch.object(subscription, 'put') as mock_put:
                self.assertEqual(MyTBAHelper.add_subscription(subscription, 'sending_device_key'), 200)
                mock_put.assert_called_once()
                mock_send_subscription_update.assert_called_once_with('user_id', 'sending_device_key')

    def test_add_subscription_200_update(self):
        subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        subscription.put()

        new_subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH])

        # Subscription exists but with different notification types - update and return 200
        with patch.object(NotificationHelper, 'send_subscription_update') as mock_send_subscription_update, \
             patch.object(subscription, 'put') as mock_put:
                self.assertEqual(MyTBAHelper.add_subscription(new_subscription), 200)
                self.assertEqual(new_subscription.notification_types, subscription.notification_types)
                mock_put.assert_called_once()
                mock_send_subscription_update.assert_called_once_with('user_id', '')

    def test_add_subscription_200_update_sending_device_key(self):
        subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        subscription.put()

        new_subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH])

        # Subscription exists but with different notification types - update and return 200
        with patch.object(NotificationHelper, 'send_subscription_update') as mock_send_subscription_update, \
             patch.object(subscription, 'put') as mock_put:
                self.assertEqual(MyTBAHelper.add_subscription(new_subscription, 'sending_device_key'), 200)
                self.assertEqual(new_subscription.notification_types, subscription.notification_types)
                mock_put.assert_called_once()
                mock_send_subscription_update.assert_called_once_with('user_id', 'sending_device_key')

    def test_remove_subscription_404(self):
        # Subscription does not exist - 404
        with patch.object(NotificationHelper, 'send_subscription_update') as mock_send_subscription_update:
            self.assertEqual(MyTBAHelper.remove_subscription('user_id', 'model_key', ModelType.TEAM), 404)
            mock_send_subscription_update.assert_not_called()

    def test_remove_subscription_200(self):
        subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        subscription_key = subscription.put()
        # Subscription does not exist - 404
        with patch.object(NotificationHelper, 'send_subscription_update') as mock_send_subscription_update, \
             patch.object(ndb, 'delete_multi') as mock_delete:
                self.assertEqual(MyTBAHelper.remove_subscription(subscription.user_id, subscription.model_key, subscription.model_type), 200)
                mock_delete.assert_called_once_with([subscription_key])
                mock_send_subscription_update.assert_called_once_with('user_id', '')

    def test_remove_subscription_200_sending_device_key(self):
        subscription = Subscription(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            model_key='frc7332',
            model_type=ModelType.TEAM)
        subscription_key = subscription.put()
        # Subscription does not exist - 404
        with patch.object(NotificationHelper, 'send_subscription_update') as mock_send_subscription_update, \
             patch.object(ndb, 'delete_multi') as mock_delete:
                self.assertEqual(MyTBAHelper.remove_subscription(subscription.user_id, subscription.model_key, subscription.model_type, 'sending_device_key'), 200)
                mock_delete.assert_called_once_with([subscription_key])
                mock_send_subscription_update.assert_called_once_with('user_id', 'sending_device_key')
