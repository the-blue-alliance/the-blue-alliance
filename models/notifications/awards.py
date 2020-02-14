from consts.award_type import AwardType

from models.notifications.notification import Notification


class AwardsNotification(Notification):

    def __init__(self, event, team=None):
        self.event = event
        self.team = team
        self.team_awards = event.team_awards().get(team.key, []) if team else []

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.AWARDS

    @property
    def fcm_notification(self):
        from firebase_admin import messaging
        # Construct Team-specific payload
        if self.team:
            if len(self.team_awards) == 1:
                award = self.team_awards[0]
                # For WINNER/FINALIST, change our verbage
                if award.award_type_enum in [AwardType.WINNER, AwardType.FINALIST]:
                    body = 'is the'
                else:
                    body = 'won the'
                body = '{} {}'.format(body, award.name_str)
            else:
                body = 'won {} awards'.format(len(self.team_awards))
            return messaging.Notification(
                title='Team {} Awards'.format(self.team.team_number),
                body='Team {} {} at the {} {}.'.format(self.team.team_number, body, self.event.year, self.event.normalized_name)
            )

        # Construct Event payload
        return messaging.Notification(
            title='{} Awards'.format(self.event.event_short.upper()),
            body='{} {} awards have been posted.'.format(self.event.year, self.event.normalized_name)
        )

    @property
    def data_payload(self):
        payload = {
            'event_key': self.event.key_name
        }

        if self.team:
            payload['team_key'] = self.team.key_name

        return payload

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['event_name'] = self.event.name

        from helpers.award_helper import AwardHelper
        from helpers.model_to_dict import ModelToDict
        if self.team:
            payload['awards'] = [ModelToDict.awardConverter(award) for award in AwardHelper.organizeAwards(self.team_awards)]
        else:
            payload['awards'] = [ModelToDict.awardConverter(award) for award in AwardHelper.organizeAwards(self.event.awards)]

        return payload
