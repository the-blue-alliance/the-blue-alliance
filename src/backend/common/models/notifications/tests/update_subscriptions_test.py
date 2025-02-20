from typing import Optional

import pytest

from backend.common.consts.client_type import ClientType
from backend.common.consts.notification_type import NotificationType
from backend.common.models.mobile_client import MobileClient
from backend.common.models.notifications.mytba import SubscriptionsUpdatedNotification


@pytest.fixture(autouse=True)
def setup(ndb_context, taskqueue_stub):
    pass


def test_type() -> None:
    assert (
        SubscriptionsUpdatedNotification._type()
        == NotificationType.UPDATE_SUBSCRIPTIONS
    )


def test_payload() -> None:
    notification = SubscriptionsUpdatedNotification("user_id", "device_id")
    assert notification.fcm_notification is None
    assert notification.data_payload is None


def test_collapse_key() -> None:
    notification = SubscriptionsUpdatedNotification("user_id", "device_id")
    platform_config = notification.platform_config
    assert platform_config is not None
    assert platform_config.collapse_key == "user_id_update_subscriptions"


@pytest.mark.parametrize(
    "user_id,notif_device_id,client_type,client_device_id,should_send",
    [
        # when no device id provided, we always sent
        ("user_id", None, ClientType.OS_ANDROID, "abc123", True),
        # when the device ids match, we should skip
        ("user_id", "abc123", ClientType.OS_ANDROID, "abc123", False),
        # when the client type is webhook, we should skip
        ("user_id", None, ClientType.WEBHOOK, "abc123", False),
    ],
)
def test_notification_shoud_skip(
    user_id: str,
    notif_device_id: Optional[str],
    client_type: ClientType,
    client_device_id: str,
    should_send: bool,
) -> None:
    notification = SubscriptionsUpdatedNotification(user_id, notif_device_id)

    client = MobileClient(
        client_type=client_type,
        device_uuid=client_device_id,
    )
    assert notification.should_send_to_client(client) == should_send
