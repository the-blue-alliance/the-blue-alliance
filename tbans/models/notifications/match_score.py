from tbans.models.notifications.notification import Notification


class MatchScoreNotification(Notification):

    def __init__(self, match):
        self.match = match
        self.event = match.event.get()
        self._event_feed = self.event.key_name
        self._district_feed = self.event.event_district_enum

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
    def platform_config(self):
        from tbans.consts.fcm.platform_priority import PlatformPriority
        from tbans.models.fcm.platform_config import PlatformConfig
        return PlatformConfig(priority=PlatformPriority.HIGH)

    @property
    def data_payload(self):
        from helpers.model_to_dict import ModelToDict
        return {
            'event_key': self.event.key_name,
            'match': ModelToDict.matchConverter(self.match)
        }

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['event_name'] = self.event.name
        return payload
