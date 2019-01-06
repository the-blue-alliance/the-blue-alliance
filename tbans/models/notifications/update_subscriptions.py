from consts.notification_type import NotificationType
from tbans.models.notifications.update_mytba import UpdateMyTBANotification


class UpdateSubscriptionsNotification(UpdateMyTBANotification):
    """ Notification dispatched to clients/webhooks when a user updates their subscriptions """

    def __init__(self, user_id, sending_device_key):
        super(UpdateSubscriptionsNotification, self).__init__(type_name='subscription', user_id=user_id, sending_device_key=sending_device_key)

    @staticmethod
    def _type():
        return NotificationType.UPDATE_SUBSCRIPTION
