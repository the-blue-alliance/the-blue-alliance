import datetime

from google.appengine.ext import ndb

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.favorite import Favorite
from backend.common.models.mobile_client import MobileClient
from backend.common.models.subscription import Subscription
from backend.common.models.suggestion import Suggestion


class AccountDeletionHelper:
    @classmethod
    def delete_account(cls, account_key: ndb.Key) -> None:
        """
        Removes all ndb models associated with the given user
        This will also delete the underlying account
        """
        user_id = str(account_key.id())

        # reject pending suggestions
        pending_suggestions_future = Suggestion.query(
            Suggestion.author == account_key,
            Suggestion.review_state == SuggestionState.REVIEW_PENDING,
        ).fetch_async()

        # fetch ndb models that we need to cascade-delete

        mobile_clients_future = MobileClient.query(
            MobileClient.user_id == user_id
        ).fetch_async(keys_only=True)
        favorites_future = Favorite.query(Favorite.user_id == user_id).fetch_async(
            keys_only=True
        )
        subscriptions_future = Subscription.query(
            Subscription.user_id == user_id
        ).fetch_async(keys_only=True)
        api_auth_access_future = ApiAuthAccess.query(
            ApiAuthAccess.owner == account_key
        ).fetch_async(keys_only=True)

        keys_to_delete = [
            account_key,
            *mobile_clients_future.get_result(),
            *favorites_future.get_result(),
            *subscriptions_future.get_result(),
            *api_auth_access_future.get_result(),
        ]

        ndb.put_multi(
            [cls._delete_suggestion(s) for s in pending_suggestions_future.get_result()]
        )
        ndb.delete_multi(keys_to_delete)

    @classmethod
    def _delete_suggestion(cls, suggestion: Suggestion) -> Suggestion:
        suggestion.review_state = SuggestionState.ACCOUNT_DELETED
        suggestion.reviewed_at = datetime.datetime.now()
        return suggestion
