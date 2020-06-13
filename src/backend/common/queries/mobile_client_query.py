from backend.common.consts.client_type import ClientType
from backend.common.futures import TypedFuture
from backend.common.models.mobile_client import MobileClient
from backend.common.queries.database_query import DatabaseQuery
from google.cloud import ndb
from typing import List


class MobileClientListQuery(DatabaseQuery[List[TypedFuture[MobileClient]]]):
    @ndb.tasklet
    def _query_async(
        self, users: List[str], client_types: List[ClientType] = list(ClientType)
    ) -> List[TypedFuture[MobileClient]]:
        if not users or not client_types:
            return []

        return (
            yield MobileClient.query(
                MobileClient.user_id.IN(users),
                MobileClient.client_type.IN(client_types),
                MobileClient.verified == True,  # noqa: E712
            ).fetch_async()
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
