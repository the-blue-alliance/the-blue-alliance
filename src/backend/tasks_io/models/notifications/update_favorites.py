from backend.tasks_io.models.notifications import Notification


class UpdateFavoritesNotification(Notification):
    @classmethod
    def _type(cls):
        from backend.common.consts.notification_type import NotificationType

        return NotificationType.UPDATE_FAVORITES
