import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.model_type import ModelType
from consts.notification_type import NotificationType

from models.account import Account
from models.subscription import Subscription


class TestSubscription(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_users_subscribed_to_event_year(self):
        # Make sure we match year*
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020*',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='2020*',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.MATCH_SCORE]
        ).put()

        users = Subscription.users_subscribed_to_event(MockEvent("2020miket", 2020), NotificationType.UPCOMING_MATCH)
        self.assertEqual(users, ['user_id_1'])

    def test_users_subscribed_to_event_key(self):
        # Make sure we event key
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020miket',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='2020mike2',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.MATCH_SCORE]
        ).put()

        users = Subscription.users_subscribed_to_event(MockEvent("2020miket", 2020), NotificationType.UPCOMING_MATCH)
        self.assertEqual(users, ['user_id_1'])

    def test_users_subscribed_to_event_year_key(self):
        # Make sure we fetch both key and year together
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020miket',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='2020*',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()

        users = Subscription.users_subscribed_to_event(MockEvent("2020miket", 2020), NotificationType.UPCOMING_MATCH)
        self.assertItemsEqual(users, ['user_id_1', 'user_id_2'])

    def test_users_subscribed_to_event_unique(self):
        # Make sure we filter for duplicates
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020miket',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020*',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()

        users = Subscription.users_subscribed_to_event(MockEvent("2020miket", 2020), NotificationType.UPCOMING_MATCH)
        self.assertEqual(users, ['user_id_1'])


class MockEvent:

    def __init__(self, key_name, year):
        self.key_name = key_name
        self.year = year
