from models.notifications.notification import Notification


class MatchVideoNotification(Notification):

    def __init__(self, match, team=None):
        self.match = match
        self.event = match.event.get()
        self.team = team

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.MATCH_VIDEO

    @property
    def fcm_notification(self):
        title = self.event.event_short.upper()
        if self.team:
            title = 'Team {}'.format(self.team.team_number)

        body = ['Video for {} {}'.format(self.event.event_short.upper(), self.match.verbose_name)]
        if self.team:
            body.append('featuring Team {}'.format(self.team.team_number))
        body.append('has been posted.')

        from firebase_admin import messaging
        return messaging.Notification(
            title='{} Match Video'.format(title),
            body=' '.join(body)
        )

    @property
    def data_payload(self):
        payload = {
            'event_key': self.event.key_name,
            'match_key': self.match.key_name
        }

        if self.team:
            payload['team_key'] = self.team.key_name

        return payload

    @property
    def webhook_message_data(self):
        from helpers.model_to_dict import ModelToDict

        payload = self.data_payload
        # Remove the FCM-only keys
        del payload['match_key']

        payload['event_name'] = self.event.name
        payload['match'] = ModelToDict.matchConverter(self.match)
        return payload
