from models.notifications.notification import Notification


class MatchScoreNotification(Notification):

    def __init__(self, match):
        self.match = match
        self.event = match.event.get()

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.MATCH_SCORE

    @property
    def fcm_notification(self):
        winning_alliance = self.match.winning_alliance
        losing_alliance = self.match.losing_alliance

        alliance_one = self.match.alliances[winning_alliance] if winning_alliance is not '' else self.match.alliances['red']
        alliance_two = self.match.alliances[losing_alliance] if losing_alliance is not '' else self.match.alliances['blue']

        # [3:] to remove 'frc' prefix
        alliance_one_teams = ', '.join([team[3:] for team in alliance_one['teams']])
        alliance_two_teams = ', '.join([team[3:] for team in alliance_two['teams']])

        alliance_one_score = alliance_one['score']
        alliance_two_score = alliance_two['score']
        if alliance_one_score == alliance_two_score:
            action = 'tied with'
        else:
            action = 'beat'

        from firebase_admin import messaging
        return messaging.Notification(
            title='{} {} Results'.format(self.event.event_short.upper(), self.match.short_name),
            body='{} {} {} scoring {}-{}.'.format(alliance_one_teams, action, alliance_two_teams, alliance_one_score, alliance_two_score)
        )

    @property
    def data_payload(self):
        print(self.match.team_key_names)
        return {
            'event_key': self.event.key_name,
            'match_key': self.match.key_name
        }

    @property
    def webhook_message_data(self):
        from helpers.model_to_dict import ModelToDict
        payload = self.data_payload
        # Remove the FCM-only keys
        del payload['match_key']
        payload['event_name'] = self.event.name
        payload['match'] = ModelToDict.matchConverter(self.match)
        return payload
