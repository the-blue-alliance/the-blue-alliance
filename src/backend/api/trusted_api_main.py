from json import JSONDecodeError

from flask import Blueprint, make_response, Response
from flask_cors import CORS

from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.trusted import (
    add_event_media,
    add_match_video,
    add_match_zebra_motionworks_info,
    delete_all_event_matches,
    delete_event_matches,
    get_event_info,
    update_event_alliances,
    update_event_awards,
    update_event_info,
    update_event_matches,
    update_event_rankings,
    update_teams,
)
from backend.common.datafeed_parsers.exceptions import ParserInputException


# Trusted API
trusted_api = Blueprint("trusted_api", __name__, url_prefix="/api/trusted/v1")
CORS(
    trusted_api,
    origins="*",
    methods=["OPTIONS", "POST"],
    allow_headers=["Content-Type", "X-TBA-Auth-Id", "X-TBA-Auth-Sig"],
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/alliance_selections/update",
    methods=["POST"],
    view_func=update_event_alliances,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/awards/update",
    methods=["POST"],
    view_func=update_event_awards,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/info",
    methods=["GET"],
    view_func=get_event_info,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/info/update",
    methods=["POST"],
    view_func=update_event_info,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/matches/update",
    methods=["POST"],
    view_func=update_event_matches,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/matches/delete",
    methods=["POST"],
    view_func=delete_event_matches,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/matches/delete_all",
    methods=["POST"],
    view_func=delete_all_event_matches,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/match_videos/add",
    methods=["POST"],
    view_func=add_match_video,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/media/add",
    methods=["POST"],
    view_func=add_event_media,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/rankings/update",
    methods=["POST"],
    view_func=update_event_rankings,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/team_list/update",
    methods=["POST"],
    view_func=update_teams,
)
trusted_api.add_url_rule(
    "/event/<string:event_key>/zebra_motionworks/add",
    methods=["POST"],
    view_func=add_match_zebra_motionworks_info,
)


@trusted_api.errorhandler(JSONDecodeError)
@trusted_api.errorhandler(ParserInputException)
def handle_bad_input(e: Exception) -> Response:
    return make_response(profiled_jsonify({"Error": f"{e}"}), 400)
