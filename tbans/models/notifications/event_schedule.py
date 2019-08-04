import calendar

from tbans.models.notifications.notification import Notification


class EventScheduleNotification(Notification):

    def __init__(self, event, next_match=None):
        self.event = event
        self._event_feed = event.key_name
        self._district_feed = event.event_district_abbrev

        if not next_match:
            from helpers.match_helper import MatchHelper
            upcoming = MatchHelper.upcomingMatches(event.matches, 1)
            self.next_match = upcoming[0] if upcoming and len(upcoming) > 0 else None
        else:
            self.next_match = next_match

    @classmethod
    def _type(cls):
        from tba.consts.notification_type import NotificationType
        return NotificationType.SCHEDULE_UPDATED

    @property
    def fcm_notification(self):
        body = 'The {} match schedule has been updated.'.format(self.event.normalized_name)
        if self.next_match and self.next_match.time:
            time = self.next_match.time.strftime("%H:%M")
            body += ' The next match starts at {}.'.format(time)

        from firebase_admin import messaging
        return messaging.Notification(
            title='{} Schedule Updated'.format(self.event.event_short.upper()),
            body=body
        )

    @property
    def platform_config(self):
        from tbans.consts.fcm.platform_priority import PlatformPriority
        from tbans.models.fcm.platform_config import PlatformConfig
        return PlatformConfig(priority=PlatformPriority.HIGH)

    @property
    def data_payload(self):
        payload = {
            'event_key': self.event.key_name
        }

        if self.next_match and self.next_match.time:
            payload['first_match_time'] = calendar.timegm(self.next_match.time.utctimetuple())
        else:
            payload['first_match_time'] = None

        return payload

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['event_name'] = self.event.name
        return payload
