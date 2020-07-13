from typing import List

from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.queries.database_query import DatabaseQuery
from backend.common.tasklets import typed_tasklet


class ApiAuthAccessQuery(DatabaseQuery[List[ApiAuthAccess]]):
    def __init__(self, owner: Account) -> None:
        super().__init__(owner=owner)

    @typed_tasklet
    def _query_async(self, owner: Account) -> List[ApiAuthAccess]:
        return (
            yield (ApiAuthAccess.query(ApiAuthAccess.owner == owner.key).fetch_async())
        )
