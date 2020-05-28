import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.award_type import AwardType
from consts.event_type import EventType
from consts.notification_type import NotificationType
from models.award import Award
from models.event import Event
from models.team import Team

from models.notifications.awards import AwardsNotification


class TestAwardsNotification(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()

        self.testbed.init_taskqueue_stub(root_path='.')

        self.event = Event(
            id='2020miket',
            event_type_enum=EventType.DISTRICT,
            short_name='Kettering University #1',
            name='FIM District Kettering University Event #1',
            event_short='miket',
            year=2020
        )

        self.team = Team(
            id='frc7332',
            team_number=7332
        )

        self.award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.INDUSTRIAL_DESIGN),
            name_str='Industrial Design Award sponsored by General Motors',
            award_type_enum=AwardType.INDUSTRIAL_DESIGN,
            event=self.event.key,
            event_type_enum=EventType.DISTRICT,
            year=2020
        )

        self.winner_award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.WINNER),
            name_str='District Event Winner',
            award_type_enum=AwardType.WINNER,
            event=self.event.key,
            event_type_enum=EventType.DISTRICT,
            year=2020
        )

    def tearDown(self):
        self.testbed.deactivate()

    def test_type(self):
        notification = AwardsNotification(self.event)
        self.assertEqual(AwardsNotification._type(), NotificationType.AWARDS)

    def test_fcm_notification_event(self):
        notification = AwardsNotification(self.event)
        self.assertIsNotNone(notification.fcm_notification)
        self.assertEqual(notification.fcm_notification.title, 'MIKET Awards')
        self.assertEqual(notification.fcm_notification.body, '2020 Kettering University #1 District awards have been posted.')

    def test_fcm_notification_team(self):
        self.award.team_list = [self.team.key]
        self.award.put()

        notification = AwardsNotification(self.event, self.team)

        self.assertIsNotNone(notification.fcm_notification)
        self.assertEqual(notification.fcm_notification.title, 'Team 7332 Awards')
        self.assertEqual(notification.fcm_notification.body, 'Team 7332 won the Industrial Design Award sponsored by General Motors at the 2020 Kettering University #1 District.')

    def test_fcm_notification_team_winner(self):
        self.winner_award.team_list = [self.team.key]
        self.winner_award.put()

        notification = AwardsNotification(self.event, self.team)

        self.assertIsNotNone(notification.fcm_notification)
        self.assertEqual(notification.fcm_notification.title, 'Team 7332 Awards')
        self.assertEqual(notification.fcm_notification.body, 'Team 7332 is the District Event Winner at the 2020 Kettering University #1 District.')

    def test_fcm_notification_team_finalist(self):
        self.winner_award.award_type_enum=AwardType.WINNER
        self.winner_award.name_str='District Event Finalist'
        self.winner_award.team_list = [self.team.key]
        self.winner_award.put()

        notification = AwardsNotification(self.event, self.team)

        self.assertIsNotNone(notification.fcm_notification)
        self.assertEqual(notification.fcm_notification.title, 'Team 7332 Awards')
        self.assertEqual(notification.fcm_notification.body, 'Team 7332 is the District Event Finalist at the 2020 Kettering University #1 District.')

    def test_fcm_notification_team_multiple(self):
        self.award.team_list = [self.team.key]
        self.award.put()
        self.winner_award.team_list = [self.team.key]
        self.winner_award.put()

        notification = AwardsNotification(self.event, self.team)

        self.assertIsNotNone(notification.fcm_notification)
        self.assertEqual(notification.fcm_notification.title, 'Team 7332 Awards')
        self.assertEqual(notification.fcm_notification.body, 'Team 7332 won 2 awards at the 2020 Kettering University #1 District.')

    def test_data_payload(self):
        notification = AwardsNotification(self.event)
        # No `event_name`
        payload = notification.data_payload
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload['event_key'], '2020miket')

    def test_data_payload_team(self):
        notification = AwardsNotification(self.event, self.team)
        payload = notification.data_payload
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload['event_key'], '2020miket')
        self.assertEqual(payload['team_key'], 'frc7332')

    def test_webhook_message_data(self):
        self.award.put()
        self.winner_award.put()

        notification = AwardsNotification(self.event)

        payload = notification.webhook_message_data
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload['event_key'], '2020miket')
        self.assertEqual(payload['event_name'], 'FIM District Kettering University Event #1')
        self.assertIsNotNone(payload['awards'])
        self.assertEqual(len(payload['awards']), 2)

    def test_webhook_message_data_team(self):
        self.award.team_list = [self.team.key]
        self.award.put()

        notification = AwardsNotification(self.event, self.team)

        payload = notification.webhook_message_data
        self.assertEqual(len(payload), 4)
        self.assertEqual(payload['event_key'], '2020miket')
        self.assertEqual(payload['team_key'], 'frc7332')
        self.assertEqual(payload['event_name'], 'FIM District Kettering University Event #1')
        self.assertIsNotNone(payload['awards'])
        self.assertEqual(len(payload['awards']), 1)
