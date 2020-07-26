from typing import Optional

from backend.common.models.account import Account
from backend.common.queries.database_query import DatabaseQuery
from backend.common.tasklets import typed_tasklet


class AccountQuery(DatabaseQuery[Optional[Account]]):
    @typed_tasklet
    def _query_async(self, email: str) -> Optional[Account]:
        if not email:
            return None
        return (yield Account.query(Account.email == email).get_async())
