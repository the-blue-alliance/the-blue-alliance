from consts.district_type import DistrictType
from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class DistrictPointsUpdatedNotification(BaseNotification):

    # disrict_key is like <year><enum>
    # Example: 2014ne
    def __init__(self, district):
        self.district_key = district.key_name
        self.district_name = district.display_name

    @property
    def _type(self):
        return NotificationType.DISTRICT_POINTS_UPDATED

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['district_key'] = self.district_key
        data['message_data']['district_name'] = self.district_name
        return data
