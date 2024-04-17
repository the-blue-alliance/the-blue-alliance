from typing import cast, List

from google.appengine.ext import ndb

from backend.common.consts.model_type import ModelType
from backend.common.consts.notification_type import NotificationType
from backend.common.consts.notification_type import (
    RENDER_NAMES as NOTIFICATION_RENDER_NAMES,
)
from backend.common.models.mytba import MyTBAModel


class Subscription(MyTBAModel):
    """
    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    notification_types: List[NotificationType] = cast(
        List[NotificationType],
        ndb.IntegerProperty(choices=list(NotificationType), repeated=True),
    )

    def __init__(self, *args, **kwargs) -> None:
        super(Subscription, self).__init__(*args, **kwargs)

    @property
    def notification_names(self) -> List[str]:
        return [
            NOTIFICATION_RENDER_NAMES[NotificationType(index)]
            for index in sorted(self.notification_types)
        ]

    @classmethod
    @ndb.tasklet
    def subscriptions_for_event(cls, event, notification_type):
        """
        Get user IDs subscribed to an Event or the year an Event occurs in and a given notification type.
        Ex: (model_key == `2020miket` or `2020*`) and (notification_type == NotificationType.UPCOMING_MATCH)

        Args:
            event (models.event.Event): The Event to query Subscription for.
            notification_type (consts.notification_type.NotificationType): A NotificationType for the Subscription.

        Returns:
            list (Subscription): List of Subscriptions to the given Event/notification type.
        """
        subscriptions = yield Subscription.query(
            Subscription.model_key.IN([event.key_name, "{}*".format(event.year)]),
            Subscription.notification_types == notification_type,
            Subscription.model_type == ModelType.EVENT,
        ).fetch_async()
        return subscriptions

    @classmethod
    @ndb.tasklet
    def subscriptions_for_team(cls, team, notification_type):
        """
        Get user IDs subscribed to a Team and a given notification type.
        Ex: team_key == `frc7332` and notification_type == NotificationType.UPCOMING_MATCH

        Args:
            team (models.team.Team): The Team to query Subscription for.
            notification_type (consts.notification_type.NotificationType): A NotificationType for the Subscription.

        Returns:
            list (Subscription): List of Subscriptions to the given Team/notification type.
            The ONLY populated field on the Subscription will be the user_id.
        """
        subscription = yield Subscription.query(
            Subscription.model_key == team.key_name,
            Subscription.notification_types == notification_type,
            Subscription.model_type == ModelType.TEAM,
        ).fetch_async()
        return subscription

    @classmethod
    @ndb.tasklet
    def subscriptions_for_match(cls, match, notification_type):
        """
        Get user IDs subscribed to a Match and a given notification type.
        Ex: team_key == `2020miket_qm1` and notification_type == NotificationType.UPCOMING_MATCH

        Args:
            match (models.match.Match): The Match to query Subscription for.
            notification_type (consts.notification_type.NotificationType): A NotificationType for the Subscription.

        Returns:
            list (Subscription): List of Subscriptions to the given Team/notification type.
        """
        subscriptions = yield Subscription.query(
            Subscription.model_key == match.key_name,
            Subscription.notification_types == notification_type,
            Subscription.model_type == ModelType.MATCH,
        ).fetch_async()
        return subscriptions
