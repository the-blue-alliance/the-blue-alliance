import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.model_type import ModelType
from consts.notification_type import NotificationType

from models.account import Account
from models.event import Event
from models.match import Match
from models.team import Team
from models.subscription import Subscription


class TestSubscription(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.event = Event(
            id='2020miket',
            event_short='miket',
            year=2020
        )
        self.team = Team(
            id='frc7332',
            team_number=7332
        )
        self.match = Match(
            id='2020miket_qm1',
            event=self.event.key,
            comp_level='qm',
            set_number=1,
            match_number=1
        )

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
        users = Subscription.users_subscribed_to_event(self.event, NotificationType.UPCOMING_MATCH)
        self.assertEqual(users, ['user_id_1'])

    def test_users_subscribed_to_event_key(self):
        # Make sure we match an event key
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

        users = Subscription.users_subscribed_to_event(self.event, NotificationType.UPCOMING_MATCH)
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
        users = Subscription.users_subscribed_to_event(self.event, NotificationType.UPCOMING_MATCH)
        self.assertItemsEqual(users, ['user_id_1', 'user_id_2'])

    def test_users_subscribed_to_event_model_type(self):
        # Make sure we filter for model types
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
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        users = Subscription.users_subscribed_to_event(self.event, NotificationType.UPCOMING_MATCH)
        self.assertItemsEqual(users, ['user_id_1'])

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
        users = Subscription.users_subscribed_to_event(self.event, NotificationType.UPCOMING_MATCH)
        self.assertEqual(users, ['user_id_1'])

    def test_users_subscribed_to_team_key(self):
        # Make sure we match a team key
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        users = Subscription.users_subscribed_to_team(self.team, NotificationType.UPCOMING_MATCH)
        self.assertItemsEqual(users, ['user_id_1', 'user_id_2'])

    def test_users_subscribed_to_team_model_type(self):
        # Make sure we filter for model types
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
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        users = Subscription.users_subscribed_to_team(self.team, NotificationType.UPCOMING_MATCH)
        self.assertItemsEqual(users, ['user_id_2'])

    def test_users_subscribed_to_team_unique(self):
        # Make sure we filter for duplicates
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()

        users = Subscription.users_subscribed_to_team(self.team, NotificationType.UPCOMING_MATCH)
        self.assertEqual(users, ['user_id_1'])

    def test_users_subscribed_to_match_key(self):
        # Make sure we match a match key
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020miket_qm1',
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='2020miket_qm1',
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        users = Subscription.users_subscribed_to_match(self.match, NotificationType.UPCOMING_MATCH)
        self.assertItemsEqual(users, ['user_id_1', 'user_id_2'])

    def test_users_subscribed_to_match_model_type(self):
        # Make sure we filter for model types
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020miket_qm1',
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='2020miket_qm1',
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        users = Subscription.users_subscribed_to_match(self.match, NotificationType.UPCOMING_MATCH)
        self.assertItemsEqual(users, ['user_id_1'])

    def test_users_subscribed_to_match_unique(self):
        # Make sure we filter for duplicates
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020miket_qm1',
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='2020miket_qm1',
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()

        users = Subscription.users_subscribed_to_match(self.match, NotificationType.UPCOMING_MATCH)
        self.assertEqual(users, ['user_id_1'])
