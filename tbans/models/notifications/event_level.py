import calendar
import datetime

from tbans.models.notifications.notification import Notification


class EventLevelNotification(Notification):

    def __init__(self, match):
        self.match = match
        self.event = match.event.get()
        self._event_feed = self.event.key_name
        self._district_feed = self.event.event_district_abbrev

    @classmethod
    def _type(cls):
        from tba.consts.notification_type import NotificationType
        return NotificationType.LEVEL_STARTING

    @property
    def fcm_notification(self):
        if self.match.time:
            time = self.match.time.strftime("%H:%M")
            ending = 'scheduled for {}.'.format(time)
        else:
            ending = 'starting.'

        from firebase_admin import messaging
        return messaging.Notification(
            title='{} {} Matches Starting'.format(self.event.event_short.upper(), self.match.full_name),
            body='{}: {} Matches are {}'.format(self.event.normalized_name, self.match.full_name, ending)
        )

    @property
    def platform_config(self):
        from tbans.consts.fcm.platform_priority import PlatformPriority
        from tbans.models.fcm.platform_config import PlatformConfig
        return PlatformConfig(priority=PlatformPriority.HIGH)

    @property
    def data_payload(self):
        payload = {
            'comp_level': self.match.comp_level,
            'event_key': self.event.key_name
        }

        if self.match.time:
            payload['scheduled_time'] = calendar.timegm(self.match.time.utctimetuple())
        else:
            payload['scheduled_time'] = None

        return payload

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['event_name'] = self.event.name
        return payload
