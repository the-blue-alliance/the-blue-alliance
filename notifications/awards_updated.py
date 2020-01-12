from consts.notification_type import NotificationType
from helpers.award_helper import AwardHelper
from helpers.model_to_dict import ModelToDict
from notifications.base_notification import BaseNotification


class AwardsUpdatedNotification(BaseNotification):

    _priority = 'high'

    def __init__(self, event):
        self.event = event

    @property
    def _type(self):
        return NotificationType.AWARDS

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.event.name
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['awards'] = [ModelToDict.awardConverter(award) for award in AwardHelper.organizeAwards(self.event.awards)]
        return data
