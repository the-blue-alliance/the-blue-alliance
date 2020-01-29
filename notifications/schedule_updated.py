import calendar

from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class ScheduleUpdatedNotification(BaseNotification):

    _priority = 'high'

    def __init__(self, event, next_match=None):
        from helpers.match_helper import MatchHelper  # recursive import issues
        self.event = event

        if not next_match:
            upcoming = MatchHelper.upcomingMatches(event.matches, 1)
            self.next_match = upcoming[0] if upcoming and len(upcoming) > 0 else None
        else:
            self.next_match = next_match

    @property
    def _type(self):
        return NotificationType.SCHEDULE_UPDATED

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['event_name'] = self.event.name
        if self.next_match and self.next_match.time:
            data['message_data']['first_match_time'] = calendar.timegm(self.next_match.time.utctimetuple())
        else:
            data['message_data']['first_match_time'] = None

        return data
