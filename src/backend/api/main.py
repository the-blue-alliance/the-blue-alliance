from flask import Flask

from backend.api.handlers.error import handle_404
from backend.api.handlers.event import event
from backend.api.handlers.team import team, team_list
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware


configure_logging()

app = Flask(__name__)
install_middleware(app)
configure_flask_cache(app)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

app.add_url_rule("/api/v3/event/<string:event_key>", view_func=event)
app.add_url_rule("/api/v3/team/<string:team_key>", view_func=team)
app.add_url_rule("/api/v3/teams/<int:page_num>", view_func=team_list)

app.register_error_handler(404, handle_404)
