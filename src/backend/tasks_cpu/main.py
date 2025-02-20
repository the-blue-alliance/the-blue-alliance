from flask import Flask
from google.appengine.api import wrap_wsgi_app

from backend.common.deferred import install_defer_routes
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.tasks_cpu.handlers.insights import blueprint as insights_blueprint
from backend.tasks_cpu.handlers.typeahead import blueprint as typeahead_blueprint


configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app, use_deferred=True)
install_middleware(app)
install_defer_routes(app)

app.register_blueprint(insights_blueprint)
app.register_blueprint(typeahead_blueprint)
