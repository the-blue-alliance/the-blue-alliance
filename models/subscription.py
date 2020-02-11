import json

from google.appengine.ext import ndb

from consts.model_type import ModelType
from consts.notification_type import NotificationType


class Subscription(ndb.Model):
    """
    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)
    model_type = ndb.IntegerProperty(required=True)
    notification_types = ndb.IntegerProperty(repeated=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        self._settings = None
        super(Subscription, self).__init__(*args, **kw)

    @property
    def notification_names(self):
        return [NotificationType.render_names[index] for index in self.notification_types]

    @classmethod
    def users_subscribed_to_event(cls, event, notification_type):
        """
        Get user IDs subscribed to an Event or the year an Event occurs in and a given notification type.
        Ex: (model_key == `2020miket` or `2020*`) and (notification_type == NotificationType.UPCOMING_MATCH)

        Args:
            event (models.event.Event): The Event to query Subscription for.
            notification_type (consts.notification_type.NotificationType): A NotificationType for the Subscription.

        Returns:
            list (string): List of user IDs with Subscriptions to the given Event/notification type.
        """
        users = Subscription.query(
            Subscription.model_key.IN([event.key_name, "{}*".format(event.year)]),
            Subscription.notification_types == notification_type,
            Subscription.model_type == ModelType.EVENT,
            projection=[Subscription.user_id]
        ).fetch()
        return list(set([user.user_id for user in users]))

    @classmethod
    def users_subscribed_to_team(cls, team, notification_type):
        """
        Get user IDs subscribed to a Team and a given notification type.
        Ex: team_key == `frc7332` and notification_type == NotificationType.UPCOMING_MATCH

        Args:
            team (models.team.Team): The Team to query Subscription for.
            notification_type (consts.notification_type.NotificationType): A NotificationType for the Subscription.

        Returns:
            list (string): List of user IDs with Subscriptions to the given Team/notification type.
        """
        users = Subscription.query(
            Subscription.model_key == team.key_name,
            Subscription.notification_types == notification_type,
            Subscription.model_type == ModelType.TEAM,
            projection=[Subscription.user_id]
        ).fetch()
        return list(set([user.user_id for user in users]))

    @classmethod
    def users_subscribed_to_match(cls, match, notification_type):
        """
        Get user IDs subscribed to a Match and a given notification type.
        Ex: team_key == `2020miket_qm1` and notification_type == NotificationType.UPCOMING_MATCH

        Args:
            match (models.match.Match): The Match to query Subscription for.
            notification_type (consts.notification_type.NotificationType): A NotificationType for the Subscription.

        Returns:
            list (string): List of user IDs with Subscriptions to the given Team/notification type.
        """
        users = Subscription.query(
            Subscription.model_key == match.key_name,
            Subscription.notification_types == notification_type,
            Subscription.model_type == ModelType.MATCH,
            projection=[Subscription.user_id]
        ).fetch()
        return list(set([user.user_id for user in users]))
