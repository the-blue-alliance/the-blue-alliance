from consts.notification_type import NotificationType
from helpers.award_helper import AwardHelper
from helpers.model_to_dict import ModelToDict
from notifications.base_notification import BaseNotification


class AwardsUpdatedNotification(BaseNotification):

    def __init__(self, event):
        self.event = event

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.AWARDS]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.event.name
        data['message_data']['event_key'] = self.event.id
        data['message_data']['awards'] = [ModelToDict.awardConverter(award) for award in AwardHelper.organizeAwards(self.event.awards)]
