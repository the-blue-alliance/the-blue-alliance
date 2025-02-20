from pyre_extensions import safe_json
from werkzeug.test import Client

from backend.api.client_api_types import (
    FavoriteCollection,
    FavoriteMessage,
    ModelPreferenceMessage,
    SubscriptionCollection,
    SubscriptionMessage,
    UpdatePreferencesInternalResponse,
    VoidRequest,
)
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.consts.model_type import ModelType
from backend.common.consts.notification_type import NotificationType
from backend.common.models.favorite import Favorite
from backend.common.models.subscription import Subscription
from backend.common.models.user import User


def test_list_favorites_no_auth(api_client: Client) -> None:
    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/favorites/list", req)
    assert resp["code"] == 401


def test_list_favorites_empty(api_client: Client, mock_clientapi_auth: User) -> None:
    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/favorites/list", req)
    assert resp == FavoriteCollection(code=200, message="", favorites=[])


def test_list_favorites(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Favorite(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
    ).put()

    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/favorites/list", req)
    assert resp == FavoriteCollection(
        code=200,
        message="",
        favorites=[FavoriteMessage(model_type=ModelType.EVENT, model_key="2023test")],
    )


def test_list_subscriptions_no_auth(api_client: Client) -> None:
    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/subscriptions/list", req)
    assert resp["code"] == 401


def test_list_subscriptions_empty(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/subscriptions/list", req)
    assert resp == SubscriptionCollection(code=200, message="", subscriptions=[])


def test_list_subscriptions(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Subscription(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
        notification_types=[NotificationType.UPCOMING_MATCH],
    ).put()

    req = VoidRequest()
    resp = make_clientapi_request(api_client, "/subscriptions/list", req)
    assert resp == SubscriptionCollection(
        code=200,
        message="",
        subscriptions=[
            SubscriptionMessage(
                model_type=ModelType.EVENT,
                model_key="2023test",
                notifications=["upcoming_match"],
            )
        ],
    )


def test_update_preferences_no_auth(api_client: Client) -> None:
    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=[],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] == 401


def test_update_preferences_set_favorite(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=True,
        notifications=[],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["favorite"]["code"] == 200

    favorite = next(
        iter(
            Favorite.query(
                Favorite.model_type == ModelType.EVENT,
                Favorite.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert favorite is not None


def test_update_preferences_set_favorite_already_exists(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Favorite(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
    ).put()

    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=True,
        notifications=[],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["favorite"]["code"] == 304

    favorite = next(
        iter(
            Favorite.query(
                Favorite.model_type == ModelType.EVENT,
                Favorite.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert favorite is not None


def test_update_preferences_remove_favorite(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Favorite(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
    ).put()

    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=[],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["favorite"]["code"] == 200

    favorite = next(
        iter(
            Favorite.query(
                Favorite.model_type == ModelType.EVENT,
                Favorite.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert favorite is None


def test_update_preferences_remove_favorite_doesnt_exist(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=[],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["favorite"]["code"] == 404

    favorite = next(
        iter(
            Favorite.query(
                Favorite.model_type == ModelType.EVENT,
                Favorite.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert favorite is None


def test_update_preferences_add_subscription(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=["upcoming_match"],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["subscription"]["code"] == 200

    subscription = next(
        iter(
            Subscription.query(
                Subscription.model_type == ModelType.EVENT,
                Subscription.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert subscription is not None
    assert subscription.notification_types == [NotificationType.UPCOMING_MATCH]


def test_update_preferences_add_subscription_already_exists(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Subscription(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
        notification_types=[NotificationType.UPCOMING_MATCH],
    ).put()

    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=["upcoming_match"],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["subscription"]["code"] == 304

    subscription = next(
        iter(
            Subscription.query(
                Subscription.model_type == ModelType.EVENT,
                Subscription.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert subscription is not None
    assert subscription.notification_types == [NotificationType.UPCOMING_MATCH]


def test_update_preferences_add_subscription_add_notification_type(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Subscription(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
        notification_types=[NotificationType.UPCOMING_MATCH],
    ).put()

    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=["upcoming_match", "match_video"],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["subscription"]["code"] == 200

    subscription = next(
        iter(
            Subscription.query(
                Subscription.model_type == ModelType.EVENT,
                Subscription.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert subscription is not None
    assert subscription.notification_types == [
        NotificationType.UPCOMING_MATCH,
        NotificationType.MATCH_VIDEO,
    ]


def test_update_preferences_add_subscription_remove_notification_type(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Subscription(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
        notification_types=[
            NotificationType.UPCOMING_MATCH,
            NotificationType.MATCH_VIDEO,
        ],
    ).put()

    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=["upcoming_match"],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["subscription"]["code"] == 200

    subscription = next(
        iter(
            Subscription.query(
                Subscription.model_type == ModelType.EVENT,
                Subscription.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert subscription is not None
    assert subscription.notification_types == [NotificationType.UPCOMING_MATCH]


def test_update_preferences_remove_subscription(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    Subscription(
        parent=mock_clientapi_auth.account_key,
        user_id=str(mock_clientapi_auth.uid),
        model_type=ModelType.EVENT,
        model_key="2023test",
        notification_types=[
            NotificationType.UPCOMING_MATCH,
        ],
    ).put()

    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=[],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["subscription"]["code"] == 200

    subscription = next(
        iter(
            Subscription.query(
                Subscription.model_type == ModelType.EVENT,
                Subscription.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert subscription is None


def test_update_preferences_remove_subscription_doesnt_exist(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = ModelPreferenceMessage(
        model_type=ModelType.EVENT,
        model_key="2023test",
        favorite=False,
        notifications=[],
        device_key="test",
    )
    resp = make_clientapi_request(api_client, "/model/setPreferences", req)
    assert resp["code"] is not None

    inner_resp = safe_json.loads(resp["message"], UpdatePreferencesInternalResponse)
    assert inner_resp["subscription"]["code"] == 404

    subscription = next(
        iter(
            Subscription.query(
                Subscription.model_type == ModelType.EVENT,
                Subscription.model_key == "2023test",
                ancestor=mock_clientapi_auth.account_key,
            ).fetch(limit=1)
        ),
        None,
    )
    assert subscription is None
