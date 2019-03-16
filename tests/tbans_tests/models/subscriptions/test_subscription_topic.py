import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from consts.model_type import ModelType
from consts.notification_type import NotificationType
from models.account import Account
from models.district import District
from models.event import Event
from models.subscription import Subscription
from models.match import Match
from models.team import Team

from tbans.models.subscriptions.subscription_topic import SubscriptionTopic


class TestSubscriptionTopic(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        # Setup "invalid" event - has already happened. Note, we do a `within_a_day` check, which means we need to set
        # this event a few days out. That's fine, TBANS-wise.
        self.invalid_event = Event(
            id="2018miket",
            event_type_enum=EventType.DISTRICT,
            name="miket",
            event_short="miket",
            year=2018,
            start_date=datetime.datetime.today() - datetime.timedelta(days=3),
            end_date=datetime.datetime.today() - datetime.timedelta(days=2)
        )
        self.invalid_event.put()

        # Setup "valid" event - happens in the future
        self.valid_event = Event(
            id="3018miket",
            event_type_enum=EventType.DISTRICT,
            name="miket",
            event_short="miket",
            year=3018,
            start_date=datetime.datetime.today() + datetime.timedelta(days=1),
            end_date=datetime.datetime.today() + datetime.timedelta(days=2)
        )
        self.valid_event.put()

        # All Teams are always valid - unless they don't exist.
        self.team = Team(
            id='frc7332',
            name='The Rawrbotz',
            team_number=7332,
            city='Anytown',
            state_prov='MI',
            postalcode='10111',
            country='USA'
        )
        self.team.put()

        self.invalid_match = Match(
            id="2018miket_f1m1",
            event=ndb.Key(Event, "2018miket"),
            year=2018,
            comp_level="f",
            set_number=1,
            match_number=1,
            team_key_names=['frc846', 'frc2135', 'frc971', 'frc254', 'frc1678', 'frc973'],
            time=datetime.datetime.fromtimestamp(1409527874),
            time_string="4:31 PM",
            alliances_json='{\
                "blue": {\
                    "score": 270,\
                    "teams": [\
                    "frc846",\
                    "frc2135",\
                    "frc971"]},\
                "red": {\
                    "score": 310,\
                    "teams": [\
                    "frc254",\
                    "frc1678",\
                    "frc973"]}}'
        )
        self.invalid_match.put()

        self.valid_match = Match(
            id="3018miket_f1m1",
            event=ndb.Key(Event, "3018miket"),
            year=3018,
            comp_level="f",
            set_number=1,
            match_number=1,
            team_key_names=['frc846', 'frc2135', 'frc971', 'frc254', 'frc1678', 'frc973'],
            time=datetime.datetime.fromtimestamp(1409527874),
            time_string="4:31 PM",
            alliances_json='{\
                "blue": {\
                    "score": -1,\
                    "teams": [\
                    "frc846",\
                    "frc2135",\
                    "frc971"]},\
                "red": {\
                    "score": -1,\
                    "teams": [\
                    "frc254",\
                    "frc1678",\
                    "frc973"]}}'
        )
        self.valid_match.put()

        self.district = District(
            id='2010fim',
            year=2010,
            abbreviation='fim',
        )
        self.district.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_user_subscription_topics_user_id_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic.user_subscription_topics(1)

    def test_user_subscription_topics_user_id_none(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic.user_subscription_topics(None)

    def test_user_subscription_topics_user_id_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic.user_subscription_topics('')

    def test_user_subscription_topics_empty(self):
        topics = SubscriptionTopic.user_subscription_topics('abc')
        self.assertEqual(topics, ['broadcast', 'abc_update_favorites', 'abc_update_subscriptions'])

    def test_user_subscription_topics(self):
        user_id = 'abc'

        # "Valid" event - only want match videos for this Event
        Subscription(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            model_key=self.valid_event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE, NotificationType.AWARDS]
        ).put()

        # "Invalid" event - happened in the past, cannot get notifications anymore
        Subscription(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            model_key=self.invalid_event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE, NotificationType.MATCH_VIDEO]
        ).put()

        topics = SubscriptionTopic.user_subscription_topics(user_id)
        self.assertEqual(topics, ['broadcast', 'abc_update_favorites', 'abc_update_subscriptions', 'event_3018miket_upcoming_match', 'event_3018miket_match_score', 'event_3018miket_awards_posted', 'event_2018miket_match_video'])

    def test_base_topics(self):
        self.assertEqual(SubscriptionTopic._base_topics(), ['broadcast'])

    def test_user_topics_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._user_topics(1)

    def test_user_topics_none(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._user_topics(None)

    def test_user_topics_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._user_topics('')

    def test_user_topics(self):
        self.assertEqual(SubscriptionTopic._user_topics('abc'), ['abc_update_favorites', 'abc_update_subscriptions'])

    def test_subscription_topics_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._subscription_topics(1)

    def test_subscription_topics_none(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._subscription_topics(None)

    def test_subscription_topics_empty(self):
        SubscriptionTopic._subscription_topics([])

    def test_subscription_topics_invalid(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._subscription_topics([1, Subscription()])

    def test_subscription_topics(self):
        user_id = 'abc'

        # "Valid" event - only want match videos for this Event
        s1 = Subscription(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            model_key=self.valid_event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE, NotificationType.AWARDS]
        )
        s1.put()

        # "Invalid" event - happened in the past, cannot get notifications anymore
        s2 = Subscription(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            model_key=self.invalid_event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE]
        )
        s2.put()

        self.assertEqual(SubscriptionTopic._subscription_topics([s1, s2]), ['event_3018miket_upcoming_match', 'event_3018miket_match_score', 'event_3018miket_awards_posted'])

    def test_valid_model_topics_model_type_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_model_topics('', 'abc', [])

    def test_valid_model_topics_model_key_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_model_topics(1, 1, [])

    def test_valid_model_topics_model_key_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._valid_model_topics(1, '', [])

    def test_valid_model_topics_notification_types_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_model_topics(1, 'abc', 1)

    def test_valid_model_topics_notification_types_invalid(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._valid_model_topics(1, 'abc', [1, ''])

    def test_valid_model_topics_notification_event(self):
        topics = SubscriptionTopic._valid_model_topics(ModelType.EVENT, self.valid_event.key_name, [NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE, NotificationType.AWARDS])
        self.assertGreater(topics, 0)

    def test_valid_model_topics_notification_team(self):
        topics = SubscriptionTopic._valid_model_topics(ModelType.TEAM, self.team.key_name, [NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE, NotificationType.AWARDS])
        self.assertGreater(topics, 0)

    def test_valid_model_topics_notification_match(self):
        topics = SubscriptionTopic._valid_model_topics(ModelType.MATCH, self.valid_match.key_name, [NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE])
        self.assertGreater(topics, 0)

    def test_valid_model_topics_notification_unsupported(self):
        district = District(
            id='2010fim',
            year=2010,
            abbreviation='fim',
        )
        district.put()

        topics = SubscriptionTopic._valid_model_topics(ModelType.DISTRICT, district.key_name, [NotificationType.UPCOMING_MATCH, NotificationType.MATCH_SCORE, NotificationType.AWARDS])
        self.assertEqual(len(topics), 0)

    def test_model_topics_model_type_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._model_topics('', 'abc', [])

    def test_model_topics_model_key_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._model_topics(1, 1, [])

    def test_model_topics_model_key_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._model_topics(1, '', [])

    def test_model_topics_notification_types_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._model_topics(1, 'abc', 1)

    def test_model_topics_notification_types_invalid(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._model_topics(1, 'abc', [1, ''])

    def test_model_topics_event(self):
        topics = SubscriptionTopic._model_topics(ModelType.EVENT, self.valid_event.key_name, [NotificationType.UPDATE_SUBSCRIPTION])
        self.assertGreater(topics, 1)

    def test_model_topics_team(self):
        topics = SubscriptionTopic._model_topics(ModelType.TEAM, self.team.key_name, [NotificationType.UPDATE_SUBSCRIPTION])
        self.assertGreater(topics, 1)

    def test_model_topics_match(self):
        topics = SubscriptionTopic._model_topics(ModelType.MATCH, self.valid_match.key_name, [NotificationType.UPDATE_SUBSCRIPTION])
        self.assertGreater(topics, 1)

    def test_model_topics_unsupported(self):
        topics = SubscriptionTopic._model_topics(ModelType.DISTRICT, self.district.key_name, [NotificationType.UPCOMING_MATCH])
        self.assertEqual(len(topics), 0)

    def test_valid_event_notifications_event_key_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_event_notifications(1, [])

    def test_valid_event_notifications_event_key_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._valid_event_notifications('', [])

    def test_valid_event_notifications_notification_types_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_event_notifications('abc', 1)

    def test_valid_event_notifications_no_event(self):
        notifications = SubscriptionTopic._valid_event_notifications('2018mike2', [NotificationType.AWARDS])
        self.assertEqual(len(notifications), 0)

    def test_valid_event_notifications_past_event(self):
        notifications = SubscriptionTopic._valid_event_notifications('2018miket', [NotificationType.AWARDS])
        self.assertEqual(len(notifications), 0)

    def test_valid_event_notifications_past_event_valid(self):
        notifications = SubscriptionTopic._valid_event_notifications('2018miket', [NotificationType.AWARDS, NotificationType.MATCH_VIDEO])
        self.assertEqual(len(notifications), 1)

    def test_valid_event_notifications_future_event(self):
        notifications = SubscriptionTopic._valid_event_notifications('3018miket', [NotificationType.AWARDS])
        self.assertEqual(len(notifications), 1)

    def test_valid_team_notifications_event_key_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_team_notifications(1, [])

    def test_valid_team_notifications_event_key_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._valid_team_notifications('', [])

    def test_valid_team_notifications_notification_types_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_team_notifications('abc', 1)

    def test_valid_team_notifications_no_team(self):
        notifications = SubscriptionTopic._valid_team_notifications('frc2337', [NotificationType.AWARDS])
        self.assertEqual(len(notifications), 0)

    def test_valid_team_notifications_team(self):
        notifications = SubscriptionTopic._valid_team_notifications('frc7332', [NotificationType.AWARDS])
        self.assertEqual(len(notifications), 1)

    # THESE IN HERE

    def test_valid_match_notifications_event_key_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_match_notifications(1, [])

    def test_valid_match_notifications_event_key_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionTopic._valid_match_notifications('', [])

    def test_valid_match_notifications_notification_types_type(self):
        with self.assertRaises(TypeError):
            SubscriptionTopic._valid_match_notifications('abc', 1)

    def test_valid_match_notifications_no_match(self):
        notifications = SubscriptionTopic._valid_match_notifications('2018miket_f1m2', [NotificationType.MATCH_VIDEO])
        self.assertEqual(len(notifications), 0)

    def test_valid_match_notifications_past_match(self):
        notifications = SubscriptionTopic._valid_match_notifications(self.invalid_match.key_name, [NotificationType.MATCH_SCORE])
        self.assertEqual(len(notifications), 0)

    def test_valid_match_notifications_past_match(self):
        notifications = SubscriptionTopic._valid_match_notifications(self.invalid_match.key_name, [NotificationType.MATCH_SCORE, NotificationType.MATCH_VIDEO])
        self.assertEqual(len(notifications), 1)

    def test_valid_match_notifications_future_match(self):
        notifications = SubscriptionTopic._valid_match_notifications(self.valid_match.key_name, [NotificationType.MATCH_SCORE, NotificationType.MATCH_VIDEO])
        self.assertEqual(len(notifications), 2)
