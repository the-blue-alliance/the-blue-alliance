import calendar

from models.notifications.notification import Notification


class MatchUpcomingNotification(Notification):

    def __init__(self, match, team=None):
        self.match = match
        self.event = match.event.get()
        self.team = team

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.UPCOMING_MATCH

    @property
    def fcm_notification(self):
        # [3:] to remove 'frc' prefix
        red_alliance = ', '.join([team[3:] for team in self.match.alliances['red']['teams']])
        blue_alliance = ', '.join([team[3:] for team in self.match.alliances['blue']['teams']])

        scheduled_time = self.match.time if self.match.predicted_time is None else self.match.predicted_time
        if scheduled_time:
            time = scheduled_time.strftime("%H:%M")
            ending = ', scheduled for {}.'.format(time)
        else:
            ending = '.'

        from firebase_admin import messaging
        return messaging.Notification(
            title='{} {} Starting Soon'.format(self.event.event_short.upper(), self.match.short_name),
            body='{} {}: {} will play {}{}'.format(self.event.normalized_name, self.match.verbose_name, red_alliance, blue_alliance, ending)
        )

    @property
    def data_payload(self):
        payload = {
            'event_key': self.event.key_name,
            'match_key': self.match.key_name,
        }

        if self.team:
            payload['team_key'] = self.team.key_name

        return payload

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['event_name'] = self.event.name
        payload['team_keys'] = self.match.team_key_names

        if self.match.time:
            payload['scheduled_time'] = calendar.timegm(self.match.time.utctimetuple())

        if self.match.predicted_time:
            payload['predicted_time'] = calendar.timegm(self.match.predicted_time.utctimetuple())

        online_webcasts = self.event.online_webcasts
        if online_webcasts:
            payload['webcast'] = online_webcasts[0]

        return payload
