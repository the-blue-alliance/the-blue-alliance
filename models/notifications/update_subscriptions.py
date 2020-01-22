from models.notifications.update_mytba import UpdateMyTBANotification


class UpdateSubscriptionsNotification(UpdateMyTBANotification):

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.UPDATE_SUBSCRIPTIONS
