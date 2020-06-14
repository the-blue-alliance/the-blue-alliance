from google.cloud import ndb
import pytest
from typing import Callable, List, Optional

from backend.common.consts.client_type import ClientType
from backend.common.models.account import Account
from backend.common.models.mobile_client import MobileClient
from backend.common.queries.mobile_client_query import MobileClientListQuery


def _client(
    user_id: str, client_type: ClientType = ClientType.OS_IOS, verified: bool = True
) -> Callable[[], MobileClient]:
    def create_client():
        client = MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id="token",
            client_type=client_type,
            device_uuid="uuid",
            display_name="Phone",
            verified=verified,
        )
        client.put()
        return client

    return create_client


@pytest.mark.parametrize(
    "clients, users, client_types, expected_users",
    [
        ([_client("abc"), _client("efg", verified=False)], [], None, []),
        ([_client("abc"), _client("efg", verified=False)], ["abc"], [], []),
        ([_client("abc"), _client("efg", verified=False)], [], [], []),
        ([_client("abc"), _client("efg", verified=False)], ["abc"], None, ["abc"]),
        ([_client("abc"), _client("efg", verified=False)], ["efg"], None, []),
        ([_client("abc"), _client("efg")], ["abc"], None, ["abc"]),
        ([_client("abc"), _client("efg")], ["abc", "efg"], None, ["abc", "efg"]),
        (
            [_client("abc"), _client("efg", ClientType.OS_ANDROID)],
            ["abc", "efg"],
            None,
            ["abc", "efg"],
        ),
        (
            [_client("abc"), _client("efg", ClientType.OS_ANDROID)],
            ["abc", "efg"],
            [ClientType.OS_IOS],
            ["abc"],
        ),
    ],
)
def test_mobile_client_list(
    clients,
    users: List[str],
    client_types: Optional[List[ClientType]],
    expected_users: List[str],
) -> None:
    clients = [client() for client in clients]
    expected = [client for client in clients if client.user_id in expected_users]
    if client_types is not None:
        mobile_clients = MobileClientListQuery(users=users, client_types=client_types)
    else:
        mobile_clients = MobileClientListQuery(users=users)
    assert mobile_clients.fetch() == expected


# def test_delete_for_messaging_id(self):
#     user_id_one = 'user_id_one'
#     messaging_id_one = 'messaging_id1'
#     messaging_id_two = 'messaging_id2'
#
#     user_id_two = 'user_id_two'
#     messaging_id_three = 'messaging_id3'
#
#     for (user_id, messaging_ids) in [(user_id_one, [messaging_id_one, messaging_id_two]), (user_id_two, [messaging_id_three])]:
#         for messaging_id in messaging_ids:
#             MobileClient(
#                 parent=ndb.Key(Account, user_id),
#                 user_id=user_id,
#                 messaging_id=messaging_id,
#                 client_type=ClientType.OS_IOS,
#                 device_uuid=messaging_id[::-1],
#                 display_name='Phone').put()
#
#     MobileClient.delete_for_messaging_id(messaging_id_one)
#
#     clients_one = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_one').fetch()]
#     clients_two = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_two').fetch()]
#
#     self.assertEqual(clients_one, [messaging_id_two])
#     self.assertEqual(clients_two, [messaging_id_three])
#
#     MobileClient.delete_for_messaging_id(messaging_id_two)
#
#     clients_one = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_one').fetch()]
#     clients_two = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_two').fetch()]
#
#     self.assertEqual(clients_one, [])
#     self.assertEqual(clients_two, [messaging_id_three])
#
#     MobileClient.delete_for_messaging_id('does_not_exist')
