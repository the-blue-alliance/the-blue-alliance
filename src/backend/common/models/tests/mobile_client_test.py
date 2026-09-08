import pytest

from backend.common.consts import client_type
from backend.common.consts.client_type import ClientType
from backend.common.consts.messaging_id_type import MessagingIdType
from backend.common.models.mobile_client import MobileClient

SHORT_ID_LENGTH = 50


@pytest.mark.parametrize("client_type, expected", client_type.NAMES.items())
def test_type_string(client_type: ClientType, expected: str) -> None:
    mobile_client = MobileClient(client_type=client_type)
    assert mobile_client.type_string == expected


@pytest.mark.parametrize("client_type", ClientType)
def test_is_webhook(client_type: ClientType) -> None:
    mobile_client = MobileClient(client_type=client_type)
    assert mobile_client.is_webhook == (client_type == ClientType.WEBHOOK)


def test_messaging_id_type_defaults_to_token() -> None:
    mobile_client = MobileClient(
        user_id="user_id",
        messaging_id="messaging_id",
        client_type=ClientType.OS_IOS,
    )
    assert mobile_client.messaging_id_type == MessagingIdType.TOKEN
    assert mobile_client.is_fid is False


@pytest.mark.parametrize("messaging_id_type", MessagingIdType)
def test_is_fid(messaging_id_type: MessagingIdType) -> None:
    mobile_client = MobileClient(
        user_id="user_id",
        messaging_id="messaging_id",
        client_type=ClientType.OS_IOS,
        messaging_id_type=messaging_id_type,
    )
    assert mobile_client.is_fid == (messaging_id_type == MessagingIdType.FID)


def test_messaging_id_type_persists(ndb_stub) -> None:
    MobileClient(
        id="fid_client",
        user_id="user_id",
        messaging_id="fid_messaging_id",
        client_type=ClientType.OS_IOS,
        messaging_id_type=MessagingIdType.FID,
    ).put()

    mobile_client = MobileClient.get_by_id("fid_client")
    assert mobile_client is not None
    assert mobile_client.messaging_id_type == MessagingIdType.FID
    assert mobile_client.is_fid is True


def test_messaging_id_type_absent_reads_back_as_token(ndb_stub) -> None:
    """Rows written before `messaging_id_type` existed must read back as TOKEN"""
    MobileClient(
        id="legacy_client",
        user_id="user_id",
        messaging_id="legacy_messaging_id",
        client_type=ClientType.OS_ANDROID_FCM,
    ).put()

    mobile_client = MobileClient.get_by_id("legacy_client")
    assert mobile_client is not None
    assert mobile_client.messaging_id_type == MessagingIdType.TOKEN
    assert mobile_client.is_fid is False


@pytest.mark.parametrize("length", range(SHORT_ID_LENGTH + 1))
def test_short_id_short(length: int) -> None:
    mobile_client = MobileClient(messaging_id=("a" * length))
    assert mobile_client.messaging_id == mobile_client.short_id


def test_short_id_long() -> None:
    length = SHORT_ID_LENGTH + 1
    mobile_client = MobileClient(messaging_id=("a" * length))
    assert len(mobile_client.messaging_id) == length
    assert mobile_client.short_id == (mobile_client.messaging_id[:50] + "...")
