from flask import Flask
from google.appengine.api import wrap_wsgi_app

from backend.common.deferred import install_defer_routes
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.tasks_io.handlers.admin.blueprint import admin_routes as admin_blueprint
from backend.tasks_io.handlers.cron_misc import blueprint as cron_misc_blueprint
from backend.tasks_io.handlers.frc_api import blueprint as frc_api_blueprint
from backend.tasks_io.handlers.live_events import blueprint as live_events_blueprint
from backend.tasks_io.handlers.math import blueprint as math_blueprint
from backend.tasks_io.handlers.nexus_api import blueprint as nexus_api_blueprint
from backend.tasks_io.handlers.tasks import blueprint as tasks_blueprint


configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app, use_deferred=True)
install_middleware(app)
install_defer_routes(app)

app.register_blueprint(admin_blueprint)
app.register_blueprint(cron_misc_blueprint)
app.register_blueprint(frc_api_blueprint)
app.register_blueprint(live_events_blueprint)
app.register_blueprint(math_blueprint)
app.register_blueprint(tasks_blueprint)
app.register_blueprint(nexus_api_blueprint)
