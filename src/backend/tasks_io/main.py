from flask import Flask
from google.appengine.api import wrap_wsgi_app

from backend.common.deferred import install_defer_routes
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.tasks_io.handlers.frc_api import blueprint as frc_api_blueprint


configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app, use_deferred=True)
install_middleware(app)
install_defer_routes(app)

app.register_blueprint(frc_api_blueprint)
