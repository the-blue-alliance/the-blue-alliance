from typing import Callable

import pytest
from google.cloud import ndb
from pyre_extensions import none_throws

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType
from backend.common.consts.client_type import ClientType
from backend.common.consts.model_type import ModelType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.favorite import Favorite
from backend.common.models.mobile_client import MobileClient
from backend.common.models.subscription import Subscription
from backend.common.models.suggestion import Suggestion
from backend.common.queries.account_query import AccountQuery
from backend.web.models.user import User


def test_init_no_email() -> None:
    user = User(session_claims={"email": ""})
    assert user._account is None


def test_init_account() -> None:
    email = "zach@thebluealliance.com"
    account = Account(email=email)
    account.put()

    user = User(session_claims={"email": email})
    assert user._account is not None


def test_init_account_uid_required() -> None:
    email = "zach@thebluealliance.com"
    with pytest.raises(KeyError, match="uid"):
        User(session_claims={"email": email})


def test_init_new_account() -> None:
    id = "abc"
    nickname = "zach"
    email = "{}@thebluealliance.com".format(nickname)

    user = User(session_claims={"uid": id, "email": email})

    assert user._account is not None
    user_account = none_throws(user._account)

    assert user_account.key.id() == id
    assert user_account.email == email
    assert not user_account.registered
    assert user_account.nickname == nickname
    assert user_account.display_name is None

    # Test that the model has been inserted in to our DB
    account = AccountQuery(email=email).fetch()
    assert account == user_account


def test_init_new_account_name() -> None:
    id = "abc"
    email = "zach@thebluealliance.com"
    name = "Zach"

    user = User(session_claims={"uid": id, "email": email, "name": name})
    assert none_throws(user._account).display_name == name


def test_email_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.email is None


def test_email() -> None:
    email = "zach@thebluealliance.com"
    account = Account(email=email)
    account.put()

    user = User(session_claims={"email": email})
    assert user.email == email


def test_display_name_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.display_name is None


def test_display_name() -> None:
    email = "zach@thebluealliance.com"
    name = "Zach"
    account = Account(email=email, display_name=name)
    account.put()

    user = User(session_claims={"email": email})
    assert user.display_name == name


def test_nickname_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.nickname is None


def test_nickname() -> None:
    email = "zach@thebluealliance.com"
    nickname = "zach"
    account = Account(email=email, nickname=nickname)
    account.put()

    user = User(session_claims={"email": email})
    assert user.nickname == nickname


def test_uid_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.uid is None


def test_uid() -> None:
    email = "zach@thebluealliance.com"
    account = Account(email=email)
    account.put()

    user = User(session_claims={"email": email})
    assert user.uid == account.key.id()


def test_account_key_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.account_key is None


def test_account_key() -> None:
    email = "zach@thebluealliance.com"
    account = Account(email=email)
    account.put()

    user = User(session_claims={"email": email})
    assert user.account_key == account.key


def test_is_registered_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert not user.is_registered


def test_is_registered_false() -> None:
    email = "zach@thebluealliance.com"
    account = Account(email=email)
    account.put()

    user = User(session_claims={"email": email})
    assert user._account is not None
    assert not user.is_registered


def test_is_registered() -> None:
    email = "zach@thebluealliance.com"
    account = Account(email=email, registered=True)
    account.put()

    user = User(session_claims={"email": email})
    assert user.is_registered


def test_permissions_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.permissions is None


def test_permissions() -> None:
    email = "zach@thebluealliance.com"
    permissions = [AccountPermission.REVIEW_MEDIA]
    account = Account(email=email, permissions=permissions)
    account.put()

    user = User(session_claims={"email": email})
    assert user.permissions == permissions


def test_mobile_clients_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.mobile_clients == []


def test_mobile_clients() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, registered=True)
    account.put()

    m1 = MobileClient(
        parent=account.key,
        user_id=account.key.id(),
        messaging_id="abc",
        client_type=ClientType.OS_IOS,
        verified=True,
    )
    m1.put()

    m2 = MobileClient(
        parent=account.key,
        user_id=account.key.id(),
        messaging_id="cde",
        client_type=ClientType.OS_IOS,
        verified=False,
    )
    m2.put()

    user = User(session_claims={"email": email})
    assert user.mobile_clients == [m1, m2]


def test_favorites_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.favorites == []


def test_favorites() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, registered=True)
    account.put()

    f = Favorite(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    f.put()

    user = User(session_claims={"email": email})
    assert user.favorites == [f]


def test_favorites_count_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.favorites_count == 0


def test_favorites_count() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, registered=True)
    account.put()

    f = Favorite(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    f.put()

    user = User(session_claims={"email": email})
    assert user.favorites_count == 1


def test_subscriptions_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.subscriptions == []


def test_subscriptions() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, registered=True)
    account.put()

    s = Subscription(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    s.put()

    user = User(session_claims={"email": email})
    assert user.subscriptions == [s]


def test_subscriptions_count_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.subscriptions_count == 0


def test_subscriptions_count() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, registered=True)
    account.put()

    s = Subscription(
        parent=account.key,
        user_id=account.key.id(),
        model_key="frc7332",
        model_type=ModelType.TEAM,
    )
    s.put()

    user = User(session_claims={"email": email})
    assert user.subscriptions_count == 1


def test_is_admin_none() -> None:
    user = User(session_claims={})
    assert not user.is_admin


def test_is_admin_false() -> None:
    user = User(session_claims={"admin": False})
    assert not user.is_admin


def test_is_admin() -> None:
    user = User(session_claims={"admin": True})
    assert user.is_admin


def test_register_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    user.register("Zach")
    assert user._account is None


def test_register() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, registered=False)
    account.put()

    user = User(session_claims={"email": email})

    assert user._account is not None
    user_account = none_throws(user._account)

    assert not user_account.registered
    assert user_account.display_name is None

    name = "Zach"
    user.register(name)
    assert user_account.registered
    assert user_account.display_name == name


def test_update_display_name_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    user.update_display_name("Zach")
    assert user._account is None


def test_update_display_name() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, registered=False)
    account.put()

    user = User(session_claims={"email": email})
    assert user._account is not None
    user_account = none_throws(user._account)

    assert not user_account.registered
    assert user_account.display_name is None

    name = "Zach"
    user.update_display_name(name)
    assert not user_account.registered
    assert user_account.display_name == name


submission_methods = (User.submissions_pending_count, User.submissions_accepted_count)


@pytest.mark.parametrize("method", submission_methods)
def test_submissions_method_count_none(method) -> None:
    user = User(session_claims={})
    assert user._account is None
    assert method.__get__(user) == 0


@pytest.mark.parametrize("method, count", zip(submission_methods, [1, 1]))
def test_submissions_method_count(method, count) -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email)
    account.put()

    for state in list(SuggestionState):
        s = Suggestion(
            review_state=state, author=account.key, target_model=SuggestionType.ROBOT
        )
        s.put()

    user = User(session_claims={"email": email})
    assert user._account is not None
    # A very gross way to indirectly call this property method
    assert method.__get__(user) == count


def test_submissions_reviewed_count_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.submissions_reviewed_count == 0


def test_submissions_reviewed_count() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email)
    account.put()

    for state in list(SuggestionState):
        s = Suggestion(
            review_state=state,
            author=account.key,
            reviewer=account.key,
            target_model=SuggestionType.ROBOT,
        )
        s.put()

    user = User(session_claims={"email": email})
    assert user._account is not None
    assert user.submissions_reviewed_count == 2


def test_has_review_permissions_none() -> None:
    user = User(session_claims={})
    assert user._account is None
    assert user.has_review_permissions is False


def test_has_review_permissions_empty() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, permissions=[])
    account.put()

    user = User(session_claims={"email": email})
    assert user._account is not None
    assert user.has_review_permissions is False


def test_has_review_permissions() -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email, permissions=[1])
    account.put()

    user = User(session_claims={"email": email})
    assert user._account is not None
    assert user.has_review_permissions is True


api_keys_method = (User.api_keys, User.api_read_keys, User.api_write_keys)


@pytest.mark.parametrize("method", api_keys_method)
def test_api_keys_method_none(method) -> None:
    user = User(session_claims={})
    assert user._account is None
    assert method.__get__(user) == []


def _api_key(auth_type: AuthType) -> Callable[[], ApiAuthAccess]:
    def create_key():
        k = ndb.Key(Account, "account")
        key = ApiAuthAccess(parent=k, owner=k, auth_types_enum=[auth_type])
        key.put()
        return key

    return create_key


@pytest.mark.parametrize(
    "method, keys",
    zip(
        api_keys_method,
        [
            [_api_key(AuthType.ZEBRA_MOTIONWORKS), _api_key(AuthType.READ_API)],
            [_api_key(AuthType.READ_API)],
            [_api_key(AuthType.ZEBRA_MOTIONWORKS)],
        ],
    ),
)
def test_api_keys_method(method, keys) -> None:
    email = "zach@thebluealliance.com"
    account = Account(id="account", email=email)
    account.put()

    expected_keys = [k() for k in keys]
    auth_types = {k.auth_types_enum[0] for k in expected_keys}
    for auth_type in {AuthType.ZEBRA_MOTIONWORKS, AuthType.READ_API} - auth_types:
        _api_key(auth_type)()

    user = User(session_claims={"email": email})
    assert user._account is not None
    assert method.__get__(user) == expected_keys
