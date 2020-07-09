from typing import List

from backend.common.consts.client_type import ClientType
from backend.common.models.mobile_client import MobileClient
from backend.common.queries.database_query import DatabaseQuery
from backend.common.tasklets import typed_tasklet


class MobileClientQuery(DatabaseQuery[List[MobileClient]]):
    def __init__(
        self,
        user_ids: List[str],
        client_types: List[ClientType] = list(ClientType),
        only_verified: bool = True,
    ) -> None:
        super().__init__(
            user_ids=user_ids, client_types=client_types, only_verified=only_verified
        )

    @typed_tasklet
    def _query_async(
        self,
        user_ids: List[str],
        client_types: List[ClientType] = list(ClientType),
        only_verified: bool = True,
    ) -> List[MobileClient]:
        if not user_ids or not client_types:
            return []

        mobile_clients_query = MobileClient.query(
            MobileClient.user_id.IN(user_ids), MobileClient.client_type.IN(client_types)
        )
        if only_verified:
            mobile_clients_query = mobile_clients_query.filter(
                MobileClient.verified == True  # noqa: E712
            )
        return (
            yield mobile_clients_query.fetch_async()
        )

    # @staticmethod
    # def delete_for_messaging_id(messaging_id):
    #     """
    #     Delete the mobile client(s) with the associated messaging_id.
    #     Args:
    #         messaging_id (string): The messaging_id to filter for.
    #     """
    #     to_delete = MobileClient.query(MobileClient.messaging_id == messaging_id).fetch(keys_only=True)
    #     ndb.delete_multi(to_delete)
