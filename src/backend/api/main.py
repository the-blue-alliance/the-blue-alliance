from json import JSONDecodeError

from flask import Blueprint, Flask, make_response, Response
from flask_cors import CORS
from google.appengine.api import wrap_wsgi_app
from werkzeug.routing import BaseConverter

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
from backend.api.handlers.district import (
    district_events,
    district_list_year,
    district_rankings,
    district_teams,
)
from backend.api.handlers.error import handle_404
from backend.api.handlers.event import (
    event,
    event_awards,
    event_detail,
    event_list_all,
    event_list_year,
    event_matches,
    event_playoff_advancement,
    event_teams,
    event_teams_statuses,
)
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.insights import (
    insights_leaderboards_all,
    insights_leaderboards_year,
    insights_notables_all,
    insights_notables_year,
)
from backend.api.handlers.match import match, zebra_motionworks
from backend.api.handlers.media import media_tags
from backend.api.handlers.status import status
from backend.api.handlers.team import (
    team,
    team_awards,
    team_event_awards,
    team_event_matches,
    team_event_status,
    team_events,
    team_events_statuses_year,
    team_history_districts,
    team_history_robots,
    team_list,
    team_list_all,
    team_matches,
    team_media_tag,
    team_media_year,
    team_social_media,
    team_years_participated,
)
from backend.api.handlers.trusted import (
    add_event_media,
    add_match_video,
    add_match_zebra_motionworks_info,
    delete_all_event_matches,
    delete_event_matches,
    update_event_alliances,
    update_event_awards,
    update_event_info,
    update_event_matches,
    update_event_rankings,
    update_teams,
)
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters


class SimpleModelTypeConverter(BaseConverter):
    regex = r"simple"


class ModelTypeConverter(BaseConverter):
    regex = r"simple|keys"


class EventDetailTypeConverter(BaseConverter):
    regex = r"alliances|district_points|insights|oprs|coprs|predictions|rankings"


configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
install_middleware(app, configure_secret_key=True)
install_url_converters(app)
configure_flask_cache(app)

app.json.compact = False  # pyre-ignore[16]
app.url_map.converters["simple_model_type"] = SimpleModelTypeConverter
app.url_map.converters["model_type"] = ModelTypeConverter
app.url_map.converters["event_detail_type"] = EventDetailTypeConverter

api_v3 = Blueprint("apiv3", __name__, url_prefix="/api/v3")
CORS(
    api_v3,
    origins="*",
    methods=["OPTIONS", "GET"],
    allow_headers=["X-TBA-Auth-Key", "If-None-Match", "If-Modified-Since"],
)

# Overall Status
api_v3.add_url_rule("/status", view_func=status)

# District
api_v3.add_url_rule("/district/<string:district_key>/events", view_func=district_events)
api_v3.add_url_rule(
    "/district/<string:district_key>/events/<model_type:model_type>",
    view_func=district_events,
)
api_v3.add_url_rule("/district/<string:district_key>/teams", view_func=district_teams)
api_v3.add_url_rule(
    "/district/<string:district_key>/teams/<model_type:model_type>",
    view_func=district_teams,
)
api_v3.add_url_rule(
    "/district/<string:district_key>/rankings", view_func=district_rankings
)

# District List
api_v3.add_url_rule("/districts/<int:year>", view_func=district_list_year)

# Event
api_v3.add_url_rule("/event/<string:event_key>", view_func=event)
api_v3.add_url_rule(
    "/event/<string:event_key>/<simple_model_type:model_type>", view_func=event
)
api_v3.add_url_rule(
    "/event/<string:event_key>/<event_detail_type:detail_type>",
    view_func=event_detail,
)
api_v3.add_url_rule("/event/<string:event_key>/teams", view_func=event_teams)
api_v3.add_url_rule(
    "/event/<string:event_key>/teams/<model_type:model_type>",
    view_func=event_teams,
)
api_v3.add_url_rule(
    "/event/<string:event_key>/teams/statuses", view_func=event_teams_statuses
)

api_v3.add_url_rule("event/<string:event_key>/matches", view_func=event_matches)
# api_v3.add_url_rule("event/<string:event_key>/matches/timeseries", view_func=TODO)
api_v3.add_url_rule(
    "/event/<string:event_key>/matches/<model_type:model_type>",
    view_func=event_matches,
)
api_v3.add_url_rule("/event/<string:event_key>/awards", view_func=event_awards)
api_v3.add_url_rule(
    "/event/<string:event_key>/playoff_advancement", view_func=event_playoff_advancement
)

# Event List
api_v3.add_url_rule("/events/all", view_func=event_list_all)
api_v3.add_url_rule("/events/all/<model_type:model_type>", view_func=event_list_all)
api_v3.add_url_rule("/events/<int:year>", view_func=event_list_year)
api_v3.add_url_rule(
    "/events/<int:year>/<model_type:model_type>", view_func=event_list_year
)

# Match
api_v3.add_url_rule("/match/<string:match_key>", view_func=match)
api_v3.add_url_rule(
    "/match/<string:match_key>/<simple_model_type:model_type>", view_func=match
)
# api_v3.add_url_rule("/match/<string:match_key>/timeseries", view_func=TODO)
api_v3.add_url_rule(
    "/match/<string:match_key>/zebra_motionworks", view_func=zebra_motionworks
)

# Media
api_v3.add_url_rule("/media/tags", view_func=media_tags)

# Team
api_v3.add_url_rule("/team/<string:team_key>", view_func=team)
api_v3.add_url_rule(
    "/team/<string:team_key>/<simple_model_type:model_type>", view_func=team
)

# Team History
api_v3.add_url_rule(
    "/team/<string:team_key>/years_participated", view_func=team_years_participated
)
api_v3.add_url_rule(
    "/team/<string:team_key>/districts", view_func=team_history_districts
)
api_v3.add_url_rule("/team/<string:team_key>/robots", view_func=team_history_robots)
api_v3.add_url_rule("/team/<string:team_key>/social_media", view_func=team_social_media)

# Team Events
api_v3.add_url_rule("/team/<string:team_key>/events", view_func=team_events)
api_v3.add_url_rule(
    "/team/<string:team_key>/events/<model_type:model_type>", view_func=team_events
)
api_v3.add_url_rule("/team/<string:team_key>/events/<int:year>", view_func=team_events)
api_v3.add_url_rule(
    "/team/<string:team_key>/events/<int:year>/<model_type:model_type>",
    view_func=team_events,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/events/<int:year>/statuses",
    view_func=team_events_statuses_year,
)

# Team @ Event
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/matches",
    view_func=team_event_matches,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/matches/<model_type:model_type>",
    view_func=team_event_matches,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/awards",
    view_func=team_event_awards,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/status",
    view_func=team_event_status,
)

# Team Awards
api_v3.add_url_rule("/team/<string:team_key>/awards", view_func=team_awards)
api_v3.add_url_rule("/team/<string:team_key>/awards/<int:year>", view_func=team_awards)

# Team Matches
api_v3.add_url_rule(
    "/team/<string:team_key>/matches/<int:year>", view_func=team_matches
)
api_v3.add_url_rule(
    "/team/<string:team_key>/matches/<int:year>/<model_type:model_type>",
    view_func=team_matches,
)

# Team Media
api_v3.add_url_rule(
    "/team/<string:team_key>/media/<int:year>", view_func=team_media_year
)
api_v3.add_url_rule(
    "/team/<string:team_key>/media/tag/<string:media_tag>", view_func=team_media_tag
)
api_v3.add_url_rule(
    "/team/<string:team_key>/media/tag/<string:media_tag>/<int:year>",
    view_func=team_media_tag,
)

# Team List
api_v3.add_url_rule("/teams/all", view_func=team_list_all)
api_v3.add_url_rule("/teams/all/<model_type:model_type>", view_func=team_list_all)
api_v3.add_url_rule("/teams/<int:page_num>", view_func=team_list)
api_v3.add_url_rule(
    "/teams/<int:page_num>/<model_type:model_type>", view_func=team_list
)
api_v3.add_url_rule("/teams/<int:year>/<int:page_num>", view_func=team_list)
api_v3.add_url_rule(
    "/teams/<int:year>/<int:page_num>/<model_type:model_type>",
    view_func=team_list,
)

# Insights
api_v3.add_url_rule("/insights/leaderboards/all", view_func=insights_leaderboards_all)
api_v3.add_url_rule(
    "/insights/leaderboards/<int:year>", view_func=insights_leaderboards_year
)
# api_v3.add_url_rule("/insights/leaderboards/<string:name>", view_func=None)
# api_v3.add_url_rule("/insights/leaderboard/<string:name>/<int:year>", view_func=None)

api_v3.add_url_rule("/insights/notables/all", view_func=insights_notables_all)
api_v3.add_url_rule("/insights/notables/<int:year>", view_func=insights_notables_year)
# api_v3.add_url_rule("/insights/notables/<string:name>", view_func=None)
# api_v3.add_url_rule("/insights/notable/<string:name>/<int:year>", view_func=None)


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


app.register_blueprint(api_v3)
app.register_blueprint(trusted_api)
app.register_blueprint(client_api)
app.register_error_handler(404, handle_404)
