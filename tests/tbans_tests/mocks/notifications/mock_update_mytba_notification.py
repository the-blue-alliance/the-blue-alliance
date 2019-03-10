from tbans.models.notifications.update_mytba import UpdateMyTBANotification


class MockUpdateMyTBANotification(UpdateMyTBANotification):

    def _type():
        return NotificationType.UPDATE_FAVORITES
