from tbans.models.notifications.update_mytba import UpdateMyTBANotification


class UpdateFavoritesNotification(UpdateMyTBANotification):
    """ Notification dispatched to clients/webhooks when a user updates their favorites """

    def __init__(self, user_id, sending_device_key):
        super(UpdateFavoritesNotification, self).__init__(type_name='favorite', user_id=user_id, sending_device_key=sending_device_key)

    @staticmethod
    def _type():
        from consts.notification_type import NotificationType
        return NotificationType.UPDATE_FAVORITES
