from models.notifications.notification import Notification


class DistrictPointsNotification(Notification):

    # disrict_key is like <year><enum>
    # Example: 2014ne
    def __init__(self, district):
        self.district = district

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.DISTRICT_POINTS_UPDATED

    @property
    def fcm_notification(self):
        from firebase_admin import messaging
        return messaging.Notification(
            title='{} District Points Updated'.format(self.district.abbreviation.upper()),
            body='{} district point calculations have been updated.'.format(self.district.display_name)
        )

    @property
    def data_payload(self):
        return {
            'district_key': self.district.key_name
        }

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['district_name'] = self.district.display_name
        return payload
