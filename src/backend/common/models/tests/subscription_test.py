from random import shuffle

from google.appengine.ext import ndb

from backend.common.consts.model_type import ModelType
from backend.common.consts.notification_type import NotificationType
from backend.common.models.account import Account
from backend.common.models.match import Match
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team
from backend.common.tests.creators.event_test_creator import EventTestCreator


def test_notification_names():
    notification_types = [
        NotificationType.MATCH_SCORE,
        NotificationType.UPCOMING_MATCH,
        NotificationType.FINAL_RESULTS,
    ]
    shuffle(notification_types)

    subscription = Subscription(notification_types=notification_types)
    # This order is important - these names should be in a sorted order
    assert subscription.notification_names == [
        "Upcoming Match",
        "Match Score",
        "Final Results",
    ]


def test_users_subscribed_to_event_year():
    event = EventTestCreator.create_future_event()
    # Make sure we match year*
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=f"{event.year}*",
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key=f"{event.year}*",
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.MATCH_SCORE]
    ).put()

    users = Subscription.users_subscribed_to_event(event, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_1']


def test_users_subscribed_to_event_key():
    event = EventTestCreator.create_future_event()
    # Make sure we match an event key
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key='2020mike2',
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_event(event, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_1']


def test_users_subscribed_to_event_year_key():
    event = EventTestCreator.create_future_event()
    # Make sure we fetch both key and year together
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key=f"{event.year}*",
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_event(event, NotificationType.UPCOMING_MATCH)
    assert sorted(users.get_result()) == ['user_id_1', 'user_id_2']


def test_users_subscribed_to_event_model_type():
    Team(
        id="frc7332",
        team_number=7332
    ).put()
    event = EventTestCreator.create_future_event()

    # Make sure we filter for model types
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key=event.teams[0].key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_event(event, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_1']


def test_users_subscribed_to_event_unique():
    event = EventTestCreator.create_future_event()
    # Make sure we filter for duplicates
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=f'{event.year}*',
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_event(event, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_1']


def test_users_subscribed_to_team_key():
    team = Team(
        id="frc7332",
        team_number=7332
    )
    team.put()

    # Make sure we match a team key
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_team(team, NotificationType.UPCOMING_MATCH)
    assert sorted(users.get_result()) == ['user_id_1', 'user_id_2']


def test_users_subscribed_to_team_model_type():
    team = Team(
        id="frc7332",
        team_number=7332
    )
    team.put()

    event = EventTestCreator.create_future_event()

    # Make sure we filter for model types
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_team(team, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_2']


def test_users_subscribed_to_team_unique():
    team = Team(
        id="frc7332",
        team_number=7332
    )
    team.put()

    # Make sure we filter for duplicates
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_team(team, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_1']


def setup_matches() -> Match:
    for team_number in range(7):
        Team(id="frc%s" % team_number, team_number=team_number).put()
    event = EventTestCreator.create_present_event()
    return event.matches[0]


def test_users_subscribed_to_match_key():
    match = setup_matches()
    # Make sure we match a match key
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_match(match, NotificationType.UPCOMING_MATCH)
    assert sorted(users.get_result()) == ['user_id_1', 'user_id_2']


def test_users_subscribed_to_match_model_type():
    match = setup_matches()
    # Make sure we filter for model types
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_2'),
        user_id='user_id_2',
        model_key=match.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_match(match, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_1']


def test_users_subscribed_to_match_unique():
    match = setup_matches()
    # Make sure we filter for duplicates
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()
    Subscription(
        parent=ndb.Key(Account, 'user_id_1'),
        user_id='user_id_1',
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH]
    ).put()

    users = Subscription.users_subscribed_to_match(match, NotificationType.UPCOMING_MATCH)
    assert users.get_result() == ['user_id_1']
