from flask import Flask
from flask_wtf.csrf import CSRFProtect
from google.appengine.api import wrap_wsgi_app

from backend.common.auth import _user_context_processor
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters
from backend.web.context_processors import render_time_context_processor
from backend.web.handlers.account import blueprint as account_blueprint
from backend.web.handlers.admin.blueprint import admin_routes as admin_blueprint
from backend.web.handlers.ajax import (
    account_apiwrite_events_handler,
    account_favorites_add_handler,
    account_favorites_delete_handler,
    account_favorites_handler,
    account_info_handler,
    account_register_fcm_token,
    event_remap_teams_handler,
    playoff_types_handler,
    typeahead_handler,
)
from backend.web.handlers.apidocs import blueprint as apidocs_blueprint
from backend.web.handlers.district import district_detail, regional_detail
from backend.web.handlers.embed import avatar_png, instagram_oembed
from backend.web.handlers.error import handle_404, handle_500
from backend.web.handlers.event import (
    event_detail,
    event_insights,
    event_list,
    event_rss,
)
from backend.web.handlers.eventwizard import eventwizard, eventwizard2
from backend.web.handlers.gameday import gameday, gameday_redirect
from backend.web.handlers.hall_of_fame import hall_of_fame_overview
from backend.web.handlers.index import about, avatar_list, index
from backend.web.handlers.insights import insights_detail, insights_overview
from backend.web.handlers.match import match_detail
from backend.web.handlers.match_suggestion import match_suggestion
from backend.web.handlers.mytba import mytba_live
from backend.web.handlers.search import search_handler
from backend.web.handlers.static import (
    add_data,
    bigquery,
    brand,
    contact,
    donate,
    opr,
    privacy,
    swag,
    thanks,
)
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
from backend.web.handlers.team_admin import (
    blueprint as team_admin,
)
from backend.web.handlers.webcasts import webcast_list
from backend.web.handlers.webhooks import (
    blueprint as webhooks,
)
from backend.web.jinja2_filters import register_template_filters
from backend.web.local.blueprint import maybe_register as maybe_install_local_routes

configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
install_middleware(app, configure_secret_key=True)
install_url_converters(app)
configure_flask_cache(app)

csrf = CSRFProtect()
csrf.init_app(app)

app.url_map.strict_slashes = False

app.add_url_rule("/", view_func=index)
app.add_url_rule("/about", view_func=about)
app.add_url_rule("/donate", view_func=donate)

app.add_url_rule("/watch/<alias>", view_func=gameday_redirect)
app.add_url_rule("/gameday/<alias>", view_func=gameday_redirect)
app.add_url_rule("/gameday", view_func=gameday)

app.add_url_rule("/event/<event_key>", view_func=event_detail)
app.add_url_rule("/event/<event_key>/feed", view_func=event_rss)
app.add_url_rule("/event/<event_key>/insights", view_func=event_insights)
app.add_url_rule("/events/<int:year>", view_func=event_list)
app.add_url_rule(
    "/events/regional",
    view_func=regional_detail,
    defaults={"year": None},
)
app.add_url_rule("/events/regional/<int:year>", view_func=regional_detail)
app.add_url_rule(
    '/events/<regex("[a-z]+"):district_abbrev>',
    view_func=district_detail,
    defaults={"year": None},
)
app.add_url_rule(
    '/events/<regex("[a-z]+"):district_abbrev>/<int:year>', view_func=district_detail
)
app.add_url_rule("/events", view_func=event_list, defaults={"year": None})

app.add_url_rule("/eventwizard", view_func=eventwizard)
app.add_url_rule("/eventwizard2", view_func=eventwizard2)

app.add_url_rule("/match/<match_key>", view_func=match_detail)

app.add_url_rule("/team/<int:team_number>", view_func=team_canonical)
app.add_url_rule("/team/<int:team_number>/<int:year>", view_func=team_detail)
app.add_url_rule("/team/<int:team_number>/history", view_func=team_history)
app.add_url_rule("/teams/<int:page>", view_func=team_list)
app.add_url_rule("/teams", view_func=team_list, defaults={"page": 1})

app.add_url_rule("/avatars", view_func=avatar_list)
app.add_url_rule("/avatars/<int:year>", view_func=avatar_list)

app.add_url_rule("/insights", view_func=insights_overview)
app.add_url_rule("/insights/<int:year>", view_func=insights_detail)

app.add_url_rule("/hall-of-fame", view_func=hall_of_fame_overview)

app.add_url_rule("/mytba", view_func=mytba_live)

app.add_url_rule("/match_suggestion", view_func=match_suggestion)

app.add_url_rule("/search", view_func=search_handler)

app.add_url_rule("/webcasts", view_func=webcast_list)
# Static pages
app.add_url_rule("/add-data", view_func=add_data)
app.add_url_rule("/brand", view_func=brand)
app.add_url_rule("/contact", view_func=contact)
app.add_url_rule("/opr", view_func=opr)
app.add_url_rule("/privacy", view_func=privacy)
app.add_url_rule("/thanks", view_func=thanks)

# Off-site redirects
app.add_url_rule("/bigquery", view_func=bigquery)
app.add_url_rule("/swag", view_func=swag)

# Ajax/Helper endpoints
app.add_url_rule(
    "/_/account/apiwrite_events", view_func=account_apiwrite_events_handler
)
app.add_url_rule(
    "/_/account/favorites/add",
    view_func=account_favorites_add_handler,
    methods=["POST"],
)
app.add_url_rule(
    "/_/account/favorites/delete",
    view_func=account_favorites_delete_handler,
    methods=["POST"],
)
app.add_url_rule(
    "/_/account/favorites/<int:model_type>", view_func=account_favorites_handler
)
app.add_url_rule(
    "/_/account/info",
    view_func=account_info_handler,
)
app.add_url_rule(
    "/_/account/register_fcm_token",
    view_func=account_register_fcm_token,
    methods=["POST"],
)
app.add_url_rule("/_/remap_teams/<event_key>", view_func=event_remap_teams_handler)
app.add_url_rule("/_/playoff_types", view_func=playoff_types_handler)
app.add_url_rule("/_/typeahead/<search_key>", view_func=typeahead_handler)
app.add_url_rule("/instagram_oembed/<media_key>", view_func=instagram_oembed)
app.add_url_rule("/avatar/<int:year>/<team_key>.png", view_func=avatar_png)

app.register_blueprint(apidocs_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(account_blueprint)
app.register_blueprint(suggestion_blueprint)
app.register_blueprint(suggestion_review_blueprint)
app.register_blueprint(team_admin)
app.register_blueprint(webhooks)

app.register_error_handler(404, handle_404)
app.register_error_handler(500, handle_500)

app.context_processor(_user_context_processor)
app.context_processor(render_time_context_processor)

register_template_filters(app)
maybe_install_local_routes(app, csrf)
