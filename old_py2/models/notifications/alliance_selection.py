from models.notifications.notification import Notification


class AllianceSelectionNotification(Notification):

    def __init__(self, event, team=None):
        self.event = event
        self.team = team

        # Find alliance for Team
        if self.team and self.event.alliance_selections:
            self.alliance = next((a for a in self.event.alliance_selections if self.team.key_name in a['picks']), None)

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.ALLIANCE_SELECTION

    @property
    def fcm_notification(self):
        body = ['{} alliances have been updated.'.format(self.event.normalized_name)]
        # Add alliance information for team
        if self.team and self.alliance:
            sub_body = ['Team {}'.format(self.team.team_number)]
            if self.alliance['picks'][0] == self.team.key_name:
                sub_body.append('is Captain of')
            else:
                sub_body.append('is on')
            # Get alliance number
            alliance_number = self.event.alliance_selections.index(self.alliance) + 1
            sub_body.append('Alliance {} with'.format(alliance_number))
            # [3:] to remove 'frc' prefix
            team_names = ['Team {}'.format(team_key[3:]) for team_key in self.alliance['picks'] if team_key != self.team.key_name]
            # A gorgeous, gramatically correct list comprehension
            # Format is like 'Team 1, Team 2, and Team 3' or just 'Team 2 and Team 3'
            sub_body.append(' and '.join([', '.join(team_names[:-1]), team_names[-1]]) + '.')
            body.append(' '.join(sub_body))

        from firebase_admin import messaging
        return messaging.Notification(
            title='{} Alliances Updated'.format(self.event.event_short.upper()),
            body=' '.join(body)
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
        from helpers.model_to_dict import ModelToDict
        payload = self.data_payload
        payload['event_name'] = self.event.name
        payload['event'] = ModelToDict.eventConverter(self.event)
        return payload
