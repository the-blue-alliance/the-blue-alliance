from typing import Optional

from google.cloud import ndb

from backend.common.models.account import Account
from backend.common.queries.database_query import DatabaseQuery


class AccountQuery(DatabaseQuery[Optional[Account]]):
    @ndb.tasklet
    def _query_async(self, email: str) -> Optional[Account]:
        if not email:
            return None
        return (
            yield Account.query(
                Account.email == email
            ).get_async()
        )
