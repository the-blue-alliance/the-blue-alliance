from flask import Flask
from flask_wtf.csrf import CSRFProtect
from google.appengine.api import wrap_wsgi_app

from backend.common.auth import _user_context_processor
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters
from backend.web.handlers.account import blueprint as account_blueprint
from backend.web.handlers.admin.blueprint import admin_routes as admin_blueprint
from backend.web.handlers.apidocs import apidocs_trusted_v1, apidocs_v3
from backend.web.handlers.district import district_detail
from backend.web.handlers.error import handle_404, handle_500
from backend.web.handlers.event import event_detail, event_list
from backend.web.handlers.gameday import gameday, gameday_redirect
from backend.web.handlers.index import about, index
from backend.web.handlers.match import match_detail
from backend.web.handlers.suggestions.suggestion_review import (
    blueprint as suggestion_review_blueprint,
)
from backend.web.handlers.suggestions.suggestion_submission import (
    blueprint as suggestion_blueprint,
)
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
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
install_middleware(app)
install_url_converters(app)
configure_flask_cache(app)

csrf = CSRFProtect()
csrf.init_app(app)

app.url_map.strict_slashes = False

app.add_url_rule("/", view_func=index)
app.add_url_rule("/about", view_func=about)
app.add_url_rule("/apidocs/trusted/v1", view_func=apidocs_trusted_v1)
app.add_url_rule("/apidocs/v3", view_func=apidocs_v3)

app.add_url_rule("/watch/<alias>", view_func=gameday_redirect)
app.add_url_rule("/gameday/<alias>", view_func=gameday_redirect)
app.add_url_rule("/gameday", view_func=gameday)

app.add_url_rule("/event/<event_key>", view_func=event_detail)
app.add_url_rule("/events/<int:year>", view_func=event_list)
app.add_url_rule(
    '/events/<regex("[a-z]+"):district_abbrev>',
    view_func=district_detail,
    defaults={"year": None},
)
app.add_url_rule(
    '/events/<regex("[a-z]+"):district_abbrev>/<int:year>', view_func=district_detail
)
app.add_url_rule("/events", view_func=event_list, defaults={"year": None})

app.add_url_rule("/match/<match_key>", view_func=match_detail)

app.add_url_rule("/team/<int:team_number>", view_func=team_canonical)
app.add_url_rule("/team/<int:team_number>/<int:year>", view_func=team_detail)
app.add_url_rule("/team/<int:team_number>/history", view_func=team_history)
app.add_url_rule("/teams/<int:page>", view_func=team_list)
app.add_url_rule("/teams", view_func=team_list, defaults={"page": 1})

app.register_blueprint(admin_blueprint)
app.register_blueprint(account_blueprint)
app.register_blueprint(suggestion_blueprint)
app.register_blueprint(suggestion_review_blueprint)

app.register_error_handler(404, handle_404)
app.register_error_handler(500, handle_500)

app.context_processor(_user_context_processor)

register_template_filters(app)
maybe_install_local_routes(app, csrf)
