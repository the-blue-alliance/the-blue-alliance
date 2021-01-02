from flask import Flask

from backend.api.handlers.error import handle_404
from backend.api.handlers.event import event
from backend.api.handlers.status import status
from backend.api.handlers.team import team, team_list, team_list_all, team_list_year
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters


configure_logging()

app = Flask(__name__)
install_middleware(app)
install_url_converters(app)
configure_flask_cache(app)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

SIMPLE_MODEL_TYPE = "<any('simple'):model_type>"
ANY_MODEL_TYPE = "<any('simple','keys'):model_type>"

# Overall Status
app.add_url_rule("/api/v3/status", view_func=status)
# Event
app.add_url_rule("/api/v3/event/<string:event_key>", view_func=event)
app.add_url_rule(
    f"/api/v3/event/<string:event_key>/{SIMPLE_MODEL_TYPE}", view_func=event
)
# Team
app.add_url_rule("/api/v3/team/<string:team_key>", view_func=team)
app.add_url_rule(f"/api/v3/team/<string:team_key>/{SIMPLE_MODEL_TYPE}", view_func=team)
# Team List
app.add_url_rule("/api/v3/teams/all", view_func=team_list_all)
app.add_url_rule(f"/api/v3/teams/all/{ANY_MODEL_TYPE}", view_func=team_list_all)
app.add_url_rule("/api/v3/teams/<int:page_num>", view_func=team_list)
app.add_url_rule(f"/api/v3/teams/<int:page_num>/{ANY_MODEL_TYPE}", view_func=team_list)
app.add_url_rule("/api/v3/teams/<int:year>/<int:page_num>", view_func=team_list_year)
app.add_url_rule(
    f"/api/v3/teams/<int:year>/<int:page_num>/{ANY_MODEL_TYPE}",
    view_func=team_list_year,
)

app.register_error_handler(404, handle_404)
