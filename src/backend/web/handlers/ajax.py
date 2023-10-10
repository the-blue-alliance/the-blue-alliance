import datetime

from flask import abort, jsonify, make_response, request, Response
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.auth import current_user
from backend.common.consts.client_type import ClientType
from backend.common.consts.model_type import ModelType
from backend.common.consts.playoff_type import TYPE_NAMES as PLAYOFF_TYPE_NAMES
from backend.common.decorators import cached_public
from backend.common.helpers.mytba_helper import MyTBAHelper
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.favorite import Favorite
from backend.common.models.keys import EventKey
from backend.common.models.mobile_client import MobileClient
from backend.common.models.typeahead_entry import TypeaheadEntry
from backend.web.decorators import enforce_login


@cached_public
def typeahead_handler(search_key: str) -> Response:
    entry = TypeaheadEntry.get_by_id(search_key)
    if entry is None:
        return jsonify([])

    response = make_response(entry.data_json)
    response.content_type = 'application/json; charset="utf-8"'
    response.last_modified = entry.updated
    return response


@enforce_login
def account_apiwrite_events_handler() -> Response:
    """
    Get the events the current user is allowed to edit via the trusted API.
    """
    user = none_throws(current_user())

    now = datetime.datetime.now()
    auth_tokens = ApiAuthAccess.query(
        ApiAuthAccess.owner == user.account_key,
        ndb.OR(
            ApiAuthAccess.expiration == None,  # noqa: E711
            ApiAuthAccess.expiration >= now,  # pyre-ignore[58]
        ),
    ).fetch()
    event_keys = []
    for token in auth_tokens:
        event_keys.extend(token.event_list)

    events = ndb.get_multi(event_keys)
    details = []
    for event in events:
        details.append(
            {"value": event.key_name, "label": "{} {}".format(event.year, event.name)}
        )
    return jsonify(details)


@cached_public
def event_remap_teams_handler(event_key: EventKey) -> Response:
    """
    Returns the current team remapping for an event
    """
    event = Event.get_by_id(event_key)
    if not event:
        return jsonify(None)

    return jsonify(event.remap_teams)


@cached_public
def playoff_types_handler() -> Response:
    """
    Returns the possible playoff types, formatted for EventWizard dropdown
    """
    types = []
    for type_enum, type_name in PLAYOFF_TYPE_NAMES.items():
        types.append({"value": type_enum, "label": type_name})
    return jsonify(types)


@enforce_login
def account_favorites_handler(model_type: int) -> Response:
    user = none_throws(current_user())
    if model_type not in set(ModelType):
        abort(400, f"Unknown model type {model_type}")

    favorites = Favorite.query(
        Favorite.model_type == model_type, ancestor=user.account_key
    ).fetch()
    return jsonify([m.to_json() for m in favorites])


@enforce_login
def account_favorites_add_handler() -> Response:
    user = none_throws(current_user())

    model_type = ModelType(int(request.form["model_type"]))
    model_key = request.form["model_key"]
    user_id = str(user.uid)

    fav = Favorite(
        parent=none_throws(user.account_key),
        user_id=user_id,
        model_type=model_type,
        model_key=model_key,
    )
    MyTBAHelper.add_favorite(fav)
    return jsonify({})


@enforce_login
def account_favorites_delete_handler() -> Response:
    user = none_throws(current_user())

    model_type = ModelType(int(request.form["model_type"]))
    model_key = request.form["model_key"]

    MyTBAHelper.remove_favorite(none_throws(user.account_key), model_key, model_type)
    return jsonify({})


def account_info_handler() -> Response:
    user = current_user()
    return jsonify(
        {
            "logged_in": (user is not None),
            "user_id": str(user.uid) if user else None,
        }
    )


@enforce_login
def account_register_fcm_token() -> Response:
    user = none_throws(current_user())
    user_id = str(user.uid)
    fcm_token = request.form.get("fcm_token")
    uuid = request.form.get("uuid")
    display_name = request.form.get("display_name")
    client_type = ClientType.WEB

    query = MobileClient.query(
        MobileClient.user_id == user_id,
        MobileClient.device_uuid == uuid,
        MobileClient.client_type == client_type,
    )
    if query.count() == 0:
        # Record doesn't exist yet, so add it
        MobileClient(
            parent=none_throws(user.account_key),
            user_id=user_id,
            messaging_id=fcm_token,
            client_type=client_type,
            device_uuid=uuid,
            display_name=display_name,
        ).put()
    else:
        client = query.fetch(1)[0]
        client.messaging_id = fcm_token
        client.display_name = display_name
        client.put()

    return jsonify({})
