from backend.common.consts.model_type import ModelType
from backend.common.models.account import Account
from backend.common.models.subscription import Subscription
from backend.common.queries.subscription_query import SubscriptionQuery


def test_no_subscriptions() -> None:
    account = Account(id="uid")
    subscriptions = SubscriptionQuery(account=account).fetch()
    assert subscriptions == []


def test_subscriptions() -> None:
    account = Account(id="uid")
    subscription = Subscription(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    subscription.put()

    subscriptions = SubscriptionQuery(account=account).fetch()
    assert subscriptions == [subscription]


def test_subscriptions_keys_only() -> None:
    account = Account(id="uid")
    subscription = Subscription(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    subscription.put()

    subscriptions = SubscriptionQuery(account=account, keys_only=True).fetch()
    assert subscriptions == [subscription.key]
