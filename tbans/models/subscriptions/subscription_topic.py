# Note: Be VERY careful modifying these.
# Modifications to these will probably mean we'll have to run some kind of migration.


class SubscriptionTopic:
    """
    Helper methods for getting topics for notification types.
    """
    @staticmethod
    def user_subscription_topics(user_id):
        """
        Get all topics for a user_id and all all Subscription objects for a user_id.
        This includes base topics, user topics, and subscription topics.

        Args:
            user_id (string): User ID to get user topics/Subscriptions for.

        Returns:
            list (string): List of valid topics for a user.
        """
        from tbans.utils.validation_utils import validate_is_string
        validate_is_string(user_id=user_id)

        from models.subscription import Subscription
        subscriptions = Subscription.user_subscriptions(user_id)

        # TODO: We could pass in a status object and flag based on the version

        subscriptions_topics = SubscriptionTopic._subscription_topics(subscriptions)
        return SubscriptionTopic._base_topics() + SubscriptionTopic._user_topics(user_id) + subscriptions_topics

    @staticmethod
    def _base_topics():
        """
        The 'base' topics a token can be subscribed to - should only contain topics with no extra formatting.

        Returns:
            list (string): List of topics that can be subscribed to.
        """
        from consts.notification_type import NotificationType
        base_notifications = [NotificationType.BROADCAST]
        return [_notification_type_name(nt) for nt in base_notifications]

    @staticmethod
    def _user_topics(user_id):
        """
        Topics tied to a user_id a token can be subscribed to.

        Args:
            user_id (string): User ID to use for namespacing topics.

        Returns:
            list (string): List of user topics that can be subscribed to.

        Raise:
            ValueError: If the user_id is not a string.
        """
        from tbans.utils.validation_utils import validate_is_string
        validate_is_string(user_id=user_id)

        from consts.notification_type import NotificationType
        user_notifications = [NotificationType.UPDATE_FAVORITES, NotificationType.UPDATE_SUBSCRIPTION]
        return ['{}_{}'.format(user_id, _notification_type_name(nt)) for nt in user_notifications]

    @staticmethod
    def _subscription_topics(subscriptions):
        """
        Get all valid topics for all Subscription objects.

        Args:
            subscriptions (list, Subscription): List of Subscriptions to get topics for.

        Returns:
            list (string): List of valid topics for Subscriptions.
        """
        from tbans.utils.validation_utils import validate_is_type
        # Ensure our subscriptions are right - non-empty list of Subscriptions.
        validate_is_type(list, not_empty=False, subscriptions=subscriptions)

        from models.subscription import Subscription
        invalid_subs = [s for s in subscriptions if not isinstance(s, Subscription)]
        if invalid_subs:
            raise ValueError('subscriptions must be Subscription objects.')

        local_topics = []
        for s in subscriptions:
            local_topics += SubscriptionTopic._valid_model_topics(s.model_type, s.model_key, s.notification_types)

        return local_topics

    @staticmethod
    def _valid_model_topics(model_type, model_key, notification_types):
        """
        Topics for a given model - will run validation to ensure we only return topics that are eligable for subscription.

        The filtering is in order to keep the # of topics we subscribe to to a minimum, since there's a hard
        limit on the # of topics an individual instance can be subscribed to.

        Args:
            model_type (int): ModelType constant from monorepo - Event, Team, Match, etc.
            model_key (string): Key for the model.
            notification_types (list, int): A list of NotificationType constants to get topics for.

        Returns:
            list (string): List of topics that can be subscribed to for the given model notification_types.
        """
        from tbans.utils.validation_utils import validate_model_params
        validate_model_params(model_type, model_key, notification_types)

        from consts.model_type import ModelType
        if model_type == ModelType.EVENT:
            valid_notification_types = SubscriptionTopic._valid_event_notifications(model_key, notification_types)
            return SubscriptionTopic._model_topics(model_type, model_key, valid_notification_types)
        elif model_type == ModelType.TEAM:
            valid_notification_types = SubscriptionTopic._valid_team_notifications(model_key, notification_types)
            return SubscriptionTopic._model_topics(model_type, model_key, valid_notification_types)
        elif model_type == ModelType.MATCH:
            valid_notification_types = SubscriptionTopic._valid_match_notifications(model_key, notification_types)
            return SubscriptionTopic._model_topics(model_type, model_key, valid_notification_types)
        else:
            return []

    @staticmethod
    def _model_topics(model_type, model_key, notification_types):
        """
        Topics for a given model - will bypass validation. This should only be used for unsubscribes.

        Args:
            model_type (int): ModelType constant from monorepo - Event, Team, Match, etc.
            model_key (string): Key for the model.
            notification_types (list, int): A list of NotificationType constants to get topics for.

        Returns:
            list (string): List of topics for the given model notification_types.
        """
        from tbans.utils.validation_utils import validate_model_params
        validate_model_params(model_type, model_key, notification_types)

        from consts.model_type import ModelType
        if model_type == ModelType.EVENT:
            return ['{}_{}'.format(model_key, _notification_type_name(nt)) for nt in notification_types]
        elif model_type == ModelType.TEAM:
            return ['{}_{}'.format(model_key, _notification_type_name(nt)) for nt in notification_types]
        elif model_type == ModelType.MATCH:
            return ['{}_{}'.format(model_key, _notification_type_name(nt)) for nt in notification_types]
        else:
            return []

    @staticmethod
    def _valid_event_notifications(event_key, notification_types):
        """
        Filter notification_types for a given event down to only notification_types that may be currently subscribed to.

        Args:
            event_key (string): Event key - in the format '[year][event_code]'.
            notification_types (list, int): A list of NotificationType constants to filter.

        Returns:
            list (int): Filtered notification_types that may be subscribed.
        """
        from tbans.utils.validation_utils import validate_model_key_and_notification_types
        validate_model_key_and_notification_types(event_key, notification_types)

        from models.event import Event
        event = Event.get_by_id(event_key)
        if not event:
            return []

        from consts.notification_type import NotificationType
        # We should only allow subscriptions to an Event if the event is still ongoing.
        # The exception to this is MATCH_VIDEO subscriptions - which can happen after the Event is over.
        if event.past:
            return _filter_valid_notification_types(notification_types, NotificationType.supported_played_event_notifications)

        return _filter_valid_notification_types(notification_types, NotificationType.supported_event_notifications)

    @staticmethod
    def _valid_team_notifications(team_key, notification_types):
        """
        Filter notification_types for a given team down to only notification_types that may be currently subscribed to.

        Args:
            team_key (string): Team key - in the format 'frcXXXX'.
            notification_types (list, int): List of NotificationType constants to filter.

        Returns:
            list (int): Filtered notification_types that may be subscribed.
        """
        from tbans.utils.validation_utils import validate_model_key_and_notification_types
        validate_model_key_and_notification_types(team_key, notification_types)

        from models.team import Team
        team = Team.get_by_id(team_key)
        if not team:
            return []

        from consts.notification_type import NotificationType
        # We should always allow subscribing to Team notifications - even if the Team is defunct, just in case
        return _filter_valid_notification_types(notification_types, NotificationType.supported_team_notifications)

    @staticmethod
    def _valid_match_notifications(match_key, notification_types):
        """
        Filter notification_types for a given match down to only notification_types that may be currently subscribed to.

        Args:
            match_key (string): Match key - in the format '[event_key]_[match_key]'.
            notification_types (list, int): List of NotificationType constants to filter.

        Returns:
            list (int): Filtered notification_types that may be subscribed.
        """
        from tbans.utils.validation_utils import validate_model_key_and_notification_types
        validate_model_key_and_notification_types(match_key, notification_types)

        from models.match import Match
        match = Match.get_by_id(match_key)
        if not match:
            return []

        from consts.notification_type import NotificationType
        # We should only allow subscriptions to a Match if the match hasn't been played yet
        # The exception to this is MATCH_VIDEO subscriptions - which can happen after a Match has been played
        if match.has_been_played:
            return _filter_valid_notification_types(notification_types, NotificationType.supported_played_match_notifications)

        return _filter_valid_notification_types(notification_types, NotificationType.supported_match_notifications)


def _notification_type_name(notification_type):
    """
    Return the string type for a NotificationType.

    Args:
        notification_type (int): The NotificationType constant to resolve a names for.

    Returns:
        string: type_name for the notification type.

    Raises:
        ValueError: If notification_type is not an int.
        KeyError: If notification_type does not have a type_name.
    """
    from tbans.utils.validation_utils import validate_is_type
    validate_is_type(int, not_empty=False, notification_type=notification_type)

    from consts.notification_type import NotificationType
    return NotificationType.type_names[notification_type]


def _filter_valid_notification_types(notification_types, valid_notification_types):
    """
    Filter a superset of notification types with a set of valid notification types.

    Args:
        notification_types (list, int): List of NotificationType constants to filter.
        valid_notification_types (list, int): List of 'valid' NotificationType constants.

    Returns:
        list (int): NotificationType constants from the notification_types that are in the valid_notification_types set.
    """
    return [n for n in notification_types if n in valid_notification_types]
