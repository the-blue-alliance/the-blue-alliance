from typing import Any, Dict, List, Optional

from google.cloud import ndb
from pyre_extensions import none_throws

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.favorite import Favorite
from backend.common.models.mobile_client import MobileClient
from backend.common.models.subscription import Subscription
from backend.common.queries.account_query import AccountQuery
from backend.common.queries.api_auth_access_query import ApiAuthAccessQuery
from backend.common.queries.favorite_query import FavoriteQuery
from backend.common.queries.mobile_client_query import MobileClientQuery
from backend.common.queries.subscription_query import SubscriptionQuery
from backend.common.queries.suggestion_query import SuggestionQuery


class User:
    def __init__(self, session_claims: Dict[str, Any]) -> None:
        self._session_claims = session_claims
        self._account: Optional[Account] = None

        email = self._session_claims.get("email")
        if not email:
            return

        self._account = AccountQuery(email=email).fetch()
        if self._account:
            return

        name = self._session_claims.get("name")
        # Get nickname from email
        nickname = email.split("@")[0]
        self._account = Account(
            id=self._session_claims["uid"],
            email=email,
            registered=False,
            nickname=nickname,
            display_name=name,
        )
        none_throws(self._account).put()

    @property
    def email(self) -> Optional[str]:
        if self._account is None:
            return None
        return none_throws(self._account).email

    @property
    def display_name(self) -> Optional[str]:
        if self._account is None:
            return None
        return none_throws(self._account).display_name

    @property
    def nickname(self) -> Optional[str]:
        if self._account is None:
            return None
        return none_throws(self._account).nickname

    @property
    def account_key(self) -> Optional[ndb.Key]:
        if self._account is None:
            return None
        return none_throws(self._account).key

    @property
    def uid(self) -> Optional[str]:
        if self._account is None:
            return None
        return none_throws(self._account).key.id()

    @property
    def is_registered(self) -> bool:
        if self._account is None:
            return False
        return none_throws(self._account).registered

    @property
    def permissions(self) -> Optional[List[AccountPermission]]:
        if self._account is None:
            return None
        return none_throws(self._account).permissions

    @property
    def mobile_clients(self) -> List[MobileClient]:
        if self._account is None:
            return []
        return MobileClientQuery(
            user_ids=[none_throws(self._account).key.id()], only_verified=False
        ).fetch()

    @property
    def favorites(self) -> List[Favorite]:
        if self._account is None:
            return []
        return FavoriteQuery(account=none_throws(self._account)).fetch()

    @property
    def favorites_count(self) -> int:
        if self._account is None:
            return 0
        return len(
            FavoriteQuery(account=none_throws(self._account), keys_only=True).fetch()
        )

    @property
    def subscriptions(self) -> List[Subscription]:
        if self._account is None:
            return []
        return SubscriptionQuery(account=none_throws(self._account)).fetch()

    @property
    def subscriptions_count(self) -> int:
        if self._account is None:
            return 0
        return len(
            SubscriptionQuery(
                account=none_throws(self._account), keys_only=True
            ).fetch()
        )

    @property
    def is_admin(self):
        return self._session_claims.get("admin", False)

    def register(self, display_name: str):
        if self._account is None:
            return
        none_throws(self._account).display_name = display_name
        none_throws(self._account).registered = True
        none_throws(self._account).put()

    def update_display_name(self, display_name: str):
        if self._account is None:
            return
        none_throws(self._account).display_name = display_name
        none_throws(self._account).put()

    @property
    def submissions_pending_count(self) -> int:
        if self._account is None:
            return 0
        return len(
            SuggestionQuery(
                review_state=SuggestionState.REVIEW_PENDING,
                author=none_throws(self._account),
                keys_only=True,
            ).fetch()
        )

    @property
    def submissions_accepted_count(self) -> int:
        if self._account is None:
            return 0
        return len(
            SuggestionQuery(
                review_state=SuggestionState.REVIEW_ACCEPTED,
                author=none_throws(self._account),
                keys_only=True,
            ).fetch()
        )

    @property
    def submissions_reviewed_count(self) -> int:
        if self._account is None:
            return 0
        review_states = [
            SuggestionState.REVIEW_ACCEPTED,
            SuggestionState.REVIEW_REJECTED,
        ]
        return sum(
            [
                len(
                    SuggestionQuery(
                        review_state=state,
                        reviewer=none_throws(self._account),
                        keys_only=True,
                    ).fetch()
                )
                for state in review_states
            ]
        )

    @property
    def has_review_permissions(self) -> bool:
        if self._account is None:
            return False
        return True if none_throws(self._account).permissions else False

    @property
    def api_keys(self) -> List[ApiAuthAccess]:
        if self._account is None:
            return []
        return ApiAuthAccessQuery(owner=none_throws(self._account)).fetch()

    @property
    def api_read_keys(self) -> List[ApiAuthAccess]:
        return list(filter(lambda key: key.is_read_key, self.api_keys))

    @property
    def api_write_keys(self) -> List[ApiAuthAccess]:
        return list(filter(lambda key: key.is_write_key, self.api_keys))
