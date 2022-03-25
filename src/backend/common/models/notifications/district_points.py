from typing import Any, Dict, Optional

from pyre_extensions import none_throws

from backend.common.consts.notification_type import NotificationType
from backend.common.models.district import District
from backend.common.models.notifications.notification import Notification


class DistrictPointsNotification(Notification):
    def __init__(self, district: District) -> None:
        self.district = district

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.DISTRICT_POINTS_UPDATED

    @property
    def fcm_notification(self) -> Optional[Any]:
        from firebase_admin import messaging

        return messaging.Notification(
            title="{} District Points Updated".format(
                self.district.abbreviation.upper()
            ),
            body="{} district point calculations have been updated.".format(
                self.district.display_name
            ),
        )

    @property
    def data_payload(self) -> Optional[Dict[str, Any]]:
        return {"district_key": self.district.key_name}

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        payload = none_throws(self.data_payload)
        payload["district_name"] = self.district.display_name
        return payload
