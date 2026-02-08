from flask import Blueprint
from flask_cors import CORS

from backend.api.handlers.client_api import (
    list_favorites,
    list_mobile_clients,
    list_subscriptions,
    ping_mobile_client,
    register_mobile_client,
    suggest_team_media,
    unregister_mobile_client,
    update_model_preferences,
)

# This is a port of the cloud endpoints API service, used by mobile apps
client_api = Blueprint("client_api", __name__, url_prefix="/clientapi/tbaClient/v9/")
CORS(
    client_api,
    origins="*",
    methods=["OPTIONS", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
client_api.add_url_rule(
    "/favorites/list",
    methods=["POST"],
    view_func=list_favorites,
)
client_api.add_url_rule(
    "/register",
    methods=["POST"],
    view_func=register_mobile_client,
)
client_api.add_url_rule(
    "/list_clients",
    methods=["POST"],
    view_func=list_mobile_clients,
)
client_api.add_url_rule(
    "/model/setPreferences",
    methods=["POST"],
    view_func=update_model_preferences,
)
client_api.add_url_rule(
    "/ping",
    methods=["POST"],
    view_func=ping_mobile_client,
)
client_api.add_url_rule(
    "/subscriptions/list",
    methods=["POST"],
    view_func=list_subscriptions,
)
client_api.add_url_rule(
    "/team/media/suggest",
    methods=["POST"],
    view_func=suggest_team_media,
)
client_api.add_url_rule(
    "/unregister",
    methods=["POST"],
    view_func=unregister_mobile_client,
)
