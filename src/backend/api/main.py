from flask import Flask
from werkzeug.routing import BaseConverter

from backend.api.handlers.error import handle_404
from backend.api.handlers.event import event, event_list_all, event_list_year
from backend.api.handlers.match import match
from backend.api.handlers.status import status
from backend.api.handlers.team import team, team_list, team_list_all, team_list_year
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters


class SimpleModelTypeConverter(BaseConverter):
    regex = r"simple"


class ModelTypeConverter(BaseConverter):
    regex = r"simple|keys"


configure_logging()

app = Flask(__name__)
install_middleware(app)
install_url_converters(app)
configure_flask_cache(app)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.url_map.converters["simple_model_type"] = SimpleModelTypeConverter
app.url_map.converters["model_type"] = ModelTypeConverter

# Overall Status
app.add_url_rule("/api/v3/status", view_func=status)
# Event
app.add_url_rule("/api/v3/event/<string:event_key>", view_func=event)
app.add_url_rule(
    "/api/v3/event/<string:event_key>/<simple_model_type:model_type>", view_func=event
)
# Event List
app.add_url_rule("/api/v3/events/all", view_func=event_list_all)
app.add_url_rule("/api/v3/events/all/<model_type:model_type>", view_func=event_list_all)
app.add_url_rule("/api/v3/events/<int:year>", view_func=event_list_year)
app.add_url_rule(
    "/api/v3/events/<int:year>/<model_type:model_type>", view_func=event_list_year
)
# Match
app.add_url_rule("/api/v3/match/<string:match_key>", view_func=match)
app.add_url_rule(
    "/api/v3/match/<string:match_key>/<simple_model_type:model_type>", view_func=match
)
# Team
app.add_url_rule("/api/v3/team/<string:team_key>", view_func=team)
app.add_url_rule(
    "/api/v3/team/<string:team_key>/<simple_model_type:model_type>", view_func=team
)
# Team List
app.add_url_rule("/api/v3/teams/all", view_func=team_list_all)
app.add_url_rule("/api/v3/teams/all/<model_type:model_type>", view_func=team_list_all)
app.add_url_rule("/api/v3/teams/<int:page_num>", view_func=team_list)
app.add_url_rule(
    "/api/v3/teams/<int:page_num>/<model_type:model_type>", view_func=team_list
)
app.add_url_rule("/api/v3/teams/<int:year>/<int:page_num>", view_func=team_list_year)
app.add_url_rule(
    "/api/v3/teams/<int:year>/<int:page_num>/<model_type:model_type>",
    view_func=team_list_year,
)

app.register_error_handler(404, handle_404)
