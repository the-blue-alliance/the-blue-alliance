from flask import Flask

from backend.common.deferred.handlers import install_defer_routes
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.common.url_converters import install_url_converters


configure_logging()

app = Flask(__name__)
install_middleware(app)
install_url_converters(app)
install_defer_routes(app)
