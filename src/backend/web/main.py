from flask import Flask

from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.web.handlers.error import handle_404, handle_500
from backend.web.handlers.gameday import gameday
from backend.web.handlers.index import index
from backend.web.handlers.team import (
    team_canonical,
    team_detail,
    team_history,
    team_list,
)
from backend.web.jinja2_filters import register_template_filters
from backend.web.local.blueprint import maybe_register as maybe_install_local_routes

configure_logging()

app = Flask(__name__)
install_middleware(app)

app.add_url_rule("/", view_func=index)
app.add_url_rule("/gameday", view_func=gameday)
app.add_url_rule("/team/<int:team_number>", view_func=team_canonical)
app.add_url_rule("/team/<int:team_number>/<int:year>", view_func=team_detail)
app.add_url_rule("/team/<int:team_number>/history", view_func=team_history)
app.add_url_rule("/teams/<int:page>", view_func=team_list)
app.add_url_rule("/teams", view_func=team_list, defaults={"page": 1})

app.register_error_handler(404, handle_404)
app.register_error_handler(500, handle_500)

register_template_filters(app)
maybe_install_local_routes(app)
