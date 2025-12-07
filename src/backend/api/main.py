from flask import Flask
from google.appengine.api import wrap_wsgi_app
from werkzeug.routing import BaseConverter

from backend.api.apiv3_main import api_v3
from backend.api.client_api_main import client_api
from backend.api.eventwizard_api_main import eventwizard_api
from backend.api.handlers.error import handle_404
from backend.api.trusted_api_main import trusted_api
from backend.common.flask_cache import configure_flask_cache
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters


class SimpleModelTypeConverter(BaseConverter):
    regex = r"simple"


class ModelTypeConverter(BaseConverter):
    regex = r"simple|keys"


class EventDetailTypeConverter(BaseConverter):
    regex = r"alliances|district_points|insights|oprs|coprs|predictions|rankings|regional_champs_pool_points"


configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
install_middleware(app, configure_secret_key=True, include_appspot_redirect=True)
install_url_converters(app)
configure_flask_cache(app)

app.json.compact = False  # pyre-ignore[16]
app.url_map.converters["simple_model_type"] = SimpleModelTypeConverter
app.url_map.converters["model_type"] = ModelTypeConverter
app.url_map.converters["event_detail_type"] = EventDetailTypeConverter


app.register_blueprint(api_v3)
app.register_blueprint(eventwizard_api)
app.register_blueprint(trusted_api)
app.register_blueprint(client_api)
app.register_error_handler(404, handle_404)
