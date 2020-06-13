import pytest

from backend.common.consts import client_type
from backend.common.consts.client_type import ClientType
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


@pytest.mark.parametrize("length", range(SHORT_ID_LENGTH + 1))
def test_short_id_short(length: int) -> None:
    mobile_client = MobileClient(messaging_id=("a" * length))
    assert mobile_client.messaging_id == mobile_client.short_id


def test_short_id_long() -> None:
    length = SHORT_ID_LENGTH + 1
    mobile_client = MobileClient(messaging_id=("a" * length))
    assert len(mobile_client.messaging_id) == length
    assert mobile_client.short_id == (mobile_client.messaging_id[:50] + "...")
