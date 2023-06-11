import pytest
from google.appengine.ext import ndb

from backend.common.consts.auth_type import AuthType
from backend.common.consts.client_type import ClientType
from backend.common.consts.model_type import ModelType
from backend.common.consts.notification_type import NotificationType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.account_deletion import AccountDeletionHelper
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.favorite import Favorite
from backend.common.models.mobile_client import MobileClient
from backend.common.models.subscription import Subscription
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)


@pytest.fixture
def account_key(ndb_stub) -> ndb.Key:
    account = Account(
        email="test@tba.com",
        registered=True,
    )
    return account.put()


def test_deletes_account(account_key) -> None:
    AccountDeletionHelper.delete_account(account_key)

    assert account_key.get() is None


def test_auto_reject_pending_suggestions(account_key) -> None:
    status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
        account_key, "http://imgur.com/ruRAxDm", "frc1124", "2016"
    )
    assert status == SuggestionCreationStatus.SUCCESS
    assert suggestion is not None

    AccountDeletionHelper.delete_account(account_key)

    suggestion = suggestion.key.get()
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.ACCOUNT_DELETED


def test_deletes_mobile_clients(account_key) -> None:
    user_id = str(account_key.id())
    MobileClient(
        user_id=user_id,
        messaging_id="abc123",
        client_type=ClientType.TEST,
    ).put()

    AccountDeletionHelper.delete_account(account_key)

    assert MobileClient.query(MobileClient.user_id == user_id).count() == 0


def test_deletes_mytba_data(account_key) -> None:
    user_id = str(account_key.id())
    Favorite(
        user_id=user_id,
        model_type=ModelType.TEAM,
        model_key="frc1124",
    ).put()
    Subscription(
        user_id=user_id,
        model_type=ModelType.TEAM,
        model_key="frc1124",
        notification_types=[NotificationType.UPCOMING_MATCH],
    ).put()

    AccountDeletionHelper.delete_account(account_key)

    assert Favorite.query(Favorite.user_id == user_id).count() == 0
    assert Subscription.query(Subscription.user_id == user_id).count() == 0


def test_deletes_api_keys(account_key) -> None:
    ApiAuthAccess(
        owner=account_key,
        auth_types_enum=[AuthType.READ_API],
    ).put()

    AccountDeletionHelper.delete_account(account_key)

    assert ApiAuthAccess.query(ApiAuthAccess.owner == account_key).count() == 0
