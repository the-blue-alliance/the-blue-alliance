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


def test_subscriptions_for_event_year():
    event = EventTestCreator.create_future_event()
    # Make sure we match year*
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=f"{event.year}*",
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key=f"{event.year}*",
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.MATCH_SCORE],
    )
    two.put()

    subscriptions_future = Subscription.subscriptions_for_event(
        event, NotificationType.UPCOMING_MATCH
    )
    subscriptions = subscriptions_future.get_result()
    assert len(subscriptions) == 1
    assert subscriptions[0].user_id == "user_id_1"


def test_subscriptions_for_event_key():
    event = EventTestCreator.create_future_event()
    # Make sure we match an event key
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key="2020mike2",
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    two.put()

    subscriptions_future = Subscription.subscriptions_for_event(
        event, NotificationType.UPCOMING_MATCH
    )
    subscriptions = subscriptions_future.get_result()
    assert len(subscriptions) == 1
    assert subscriptions[0].user_id == "user_id_1"


def test_subscriptions_for_event_year_key():
    event = EventTestCreator.create_future_event()
    # Make sure we fetch both key and year together
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key=f"{event.year}*",
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    two.put()

    subscriptions_future = Subscription.subscriptions_for_event(
        event, NotificationType.UPCOMING_MATCH
    )
    subscriptions = subscriptions_future.get_result()
    assert len(subscriptions) == 2
    assert one in subscriptions
    assert two in subscriptions


def test_subscriptions_for_event_model_type():
    Team(id="frc7332", team_number=7332).put()
    event = EventTestCreator.create_future_event()

    # Make sure we filter for model types
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key=event.teams[0].key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    two.put()

    subscriptions_future = Subscription.subscriptions_for_event(
        event, NotificationType.UPCOMING_MATCH
    )
    subscriptions = subscriptions_future.get_result()
    assert len(subscriptions) == 1
    assert subscriptions[0].user_id == "user_id_1"


# def test_subscriptions_for_event_distinct():
#     event = EventTestCreator.create_future_event()
#     # Make sure we filter for duplicates
#     one = Subscription(
#         parent=ndb.Key(Account, 'user_id_1'),
#         user_id='user_id_1',
#         model_key=event.key_name,
#         model_type=ModelType.EVENT,
#         notification_types=[NotificationType.UPCOMING_MATCH]
#     )
#     one.put()
#     two = Subscription(
#         parent=ndb.Key(Account, 'user_id_1'),
#         user_id='user_id_1',
#         model_key=f'{event.year}*',
#         model_type=ModelType.EVENT,
#         notification_types=[NotificationType.UPCOMING_MATCH]
#     )
#     two.put()

#     subscriptions_future = Subscription.subscriptions_for_event(event, NotificationType.UPCOMING_MATCH)
#     subscriptions = subscriptions_future.get_result()
#     assert len(subscriptions) == 1
#     assert subscriptions[0].user_id == "user_id_1"


def test_subscriptions_for_team_key():
    team = Team(id="frc7332", team_number=7332)
    team.put()

    # Make sure we match a team key
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    two.put()

    subscriptions_future = Subscription.subscriptions_for_team(
        team, NotificationType.UPCOMING_MATCH
    )
    subscriptions = subscriptions_future.get_result()
    assert len(subscriptions) == 2
    assert one in subscriptions
    assert two in subscriptions


def test_subscriptions_for_team_model_type():
    team = Team(id="frc7332", team_number=7332)
    team.put()

    event = EventTestCreator.create_future_event()

    # Make sure we filter for model types
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=event.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key=team.key_name,
        model_type=ModelType.TEAM,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    two.put()

    subscriptions = Subscription.subscriptions_for_team(
        team, NotificationType.UPCOMING_MATCH
    )
    assert subscriptions.get_result() == [two]


# def test_subscriptions_for_team_distinct():
#     team = Team(
#         id="frc7332",
#         team_number=7332
#     )
#     team.put()

#     # Make sure we filter for duplicates
#     one = Subscription(
#         parent=ndb.Key(Account, 'user_id_1'),
#         user_id='user_id_1',
#         model_key=team.key_name,
#         model_type=ModelType.TEAM,
#         notification_types=[NotificationType.UPCOMING_MATCH]
#     )
#     one.put()
#     two = Subscription(
#         parent=ndb.Key(Account, 'user_id_1'),
#         user_id='user_id_1',
#         model_key=team.key_name,
#         model_type=ModelType.TEAM,
#         notification_types=[NotificationType.UPCOMING_MATCH]
#     )
#     two.put()

#     subscriptions_future = Subscription.subscriptions_for_team(team, NotificationType.UPCOMING_MATCH)
#     subscriptions = subscriptions_future.get_result()
#     assert len(subscriptions) == 1
#     assert subscriptions[0].user_id == "user_id_1"


def setup_matches() -> Match:
    for team_number in range(7):
        Team(id="frc%s" % team_number, team_number=team_number).put()
    event = EventTestCreator.create_present_event()
    return event.matches[0]


def test_subscriptions_for_match_key():
    match = setup_matches()
    # Make sure we match a match key
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    two.put()

    subscriptions_future = Subscription.subscriptions_for_match(
        match, NotificationType.UPCOMING_MATCH
    )
    subscriptions = subscriptions_future.get_result()
    assert len(subscriptions) == 2
    assert one in subscriptions
    assert two in subscriptions


def test_subscriptions_for_match_model_type():
    match = setup_matches()
    # Make sure we filter for model types
    one = Subscription(
        parent=ndb.Key(Account, "user_id_1"),
        user_id="user_id_1",
        model_key=match.key_name,
        model_type=ModelType.MATCH,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    one.put()
    two = Subscription(
        parent=ndb.Key(Account, "user_id_2"),
        user_id="user_id_2",
        model_key=match.key_name,
        model_type=ModelType.EVENT,
        notification_types=[NotificationType.UPCOMING_MATCH],
    )
    two.put()

    subscriptions = Subscription.subscriptions_for_match(
        match, NotificationType.UPCOMING_MATCH
    )
    assert subscriptions.get_result() == [one]


# def test_subscriptions_for_match_distinct():
#     match = setup_matches()
#     # Make sure we filter for duplicates
#     one = Subscription(
#         parent=ndb.Key(Account, 'user_id_1'),
#         user_id='user_id_1',
#         model_key=match.key_name,
#         model_type=ModelType.MATCH,
#         notification_types=[NotificationType.UPCOMING_MATCH]
#     )
#     one.put()
#     two = Subscription(
#         parent=ndb.Key(Account, 'user_id_1'),
#         user_id='user_id_1',
#         model_key=match.key_name,
#         model_type=ModelType.MATCH,
#         notification_types=[NotificationType.UPCOMING_MATCH]
#     )
#     two.put()

#     subscriptions_future = Subscription.subscriptions_for_match(match, NotificationType.UPCOMING_MATCH)
#     subscriptions = subscriptions_future.get_result()
#     assert len(subscriptions) == 1
#     assert subscriptions[0].user_id == "user_id_1"
