from collections.abc import Generator
from typing import Any

from backend.common.models.account import Account
from backend.common.queries.database_query import DatabaseQuery
from backend.common.tasklets import typed_tasklet


class AccountQuery(DatabaseQuery[Account | None, None]):
    DICT_CONVERTER = None

    @typed_tasklet
    def _query_async(self, email: str) -> Generator[Any, Any, Account | None]:
        if not email:
            return None
        return (yield Account.query(Account.email == email).get_async())
