from flask import Blueprint
from flask_cors import CORS

from backend.api.handlers.moderation import (
    moderation_queue,
    moderation_suggestion_accept,
    moderation_suggestion_list,
    moderation_suggestions_reject,
)

# Authenticated API for site moderators to review the suggestion queue.
# Auth is a Firebase ID token (Authorization: Bearer), the same mechanism as
# the client API; authorization is the account's AccountPermission flags.
moderation_api = Blueprint("moderation_api", __name__, url_prefix="/api/moderation/v1")
CORS(
    moderation_api,
    origins="*",
    methods=["OPTIONS", "GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
moderation_api.add_url_rule(
    "/queue",
    methods=["GET"],
    view_func=moderation_queue,
)
moderation_api.add_url_rule(
    "/suggestions/<suggestion_type>",
    methods=["GET"],
    view_func=moderation_suggestion_list,
)
moderation_api.add_url_rule(
    "/suggestions/<suggestion_key>/accept",
    methods=["POST"],
    view_func=moderation_suggestion_accept,
)
moderation_api.add_url_rule(
    "/suggestions/reject",
    methods=["POST"],
    view_func=moderation_suggestions_reject,
)
