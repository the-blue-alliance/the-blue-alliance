from json import JSONDecodeError

from flask import Blueprint, Flask, jsonify, make_response, Response
from flask_cors import CORS
from google.appengine.api import wrap_wsgi_app

from backend.api.handlers.error import handle_404
from backend.api.handlers.event import event
from backend.api.handlers.status import status
from backend.api.handlers.team import team, team_list, team_list_all, team_list_year
from backend.api.handlers.trusted import (
    add_match_video,
    delete_all_event_matches,
    delete_event_matches,
    update_event_alliances,
    update_event_awards,
    update_event_info,
    update_event_matches,
    update_teams,
)
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters


configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
install_middleware(app)
install_url_converters(app)
configure_flask_cache(app)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

SIMPLE_MODEL_TYPE = "<any('simple'):model_type>"
ANY_MODEL_TYPE = "<any('simple','keys'):model_type>"

api_v3 = Blueprint("apiv3", __name__, url_prefix="/api/v3")
CORS(api_v3, origins="*", methods=["OPTIONS", "GET"], allow_headers=["X-TBA-Auth-Key"])

# Overall Status
api_v3.add_url_rule("/status", view_func=status)
# Event
api_v3.add_url_rule("/event/<string:event_key>", view_func=event)
# Team
api_v3.add_url_rule("/team/<string:team_key>", view_func=team)
api_v3.add_url_rule(f"/team/<string:team_key>/{SIMPLE_MODEL_TYPE}", view_func=team)
# Team List
api_v3.add_url_rule("/teams/all", view_func=team_list_all)
api_v3.add_url_rule(f"/teams/all/{ANY_MODEL_TYPE}", view_func=team_list_all)
api_v3.add_url_rule("/teams/<int:page_num>", view_func=team_list)
api_v3.add_url_rule(f"/teams/<int:page_num>/{ANY_MODEL_TYPE}", view_func=team_list)
api_v3.add_url_rule("/teams/<int:year>/<int:page_num>", view_func=team_list_year)
api_v3.add_url_rule(
    f"/teams/<int:year>/<int:page_num>/{ANY_MODEL_TYPE}",
    view_func=team_list_year,
)

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
),
trusted_api.add_url_rule(
    "/event/<string:event_key>/awards/update",
    methods=["POST"],
    view_func=update_event_awards,
),
trusted_api.add_url_rule(
    "/event/<string:event_key>/info/update",
    methods=["POST"],
    view_func=update_event_info,
),
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
    "/event/<string:event_key>/team_list/update",
    methods=["POST"],
    view_func=update_teams,
)


@trusted_api.errorhandler(JSONDecodeError)
@trusted_api.errorhandler(ParserInputException)
def handle_bad_input(e: Exception) -> Response:
    return make_response(jsonify({"Error": f"{e}"}), 400)


app.register_blueprint(api_v3)
app.register_blueprint(trusted_api)
app.register_error_handler(404, handle_404)
