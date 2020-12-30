from flask import Flask

from backend.common.deferred.handlers import install_defer_routes
from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware


configure_logging()

app = Flask(__name__)
install_middleware(app)
install_defer_routes(app)
