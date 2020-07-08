from typing import List

from backend.common.models.account import Account
from backend.common.models.subscription import Subscription
from backend.common.queries.database_query import DatabaseQuery
from backend.common.tasklets import typed_tasklet


class SubscriptionQuery(DatabaseQuery[List[Subscription]]):
    def __init__(self, account: Account, keys_only: bool = False) -> None:
        super().__init__(account=account, keys_only=keys_only)

    @typed_tasklet
    def _query_async(
        self, account: Account, keys_only: bool = False
    ) -> List[Subscription]:
        subscription_query = Subscription.query(ancestor=account.key)
        return (yield (subscription_query.fetch_async(keys_only=keys_only)))
