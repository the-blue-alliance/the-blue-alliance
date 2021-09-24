import logging
from flask import Flask

from backend.common.deferred.handlers import install_defer_routes
from backend.common.logging import configure_logging
from backend.common.middleware import install_backend_security, install_middleware


configure_logging()

app = Flask(__name__)
install_middleware(app)
install_backend_security(app)
install_defer_routes(app)


@app.route('/tasks-io/test')
def test():
    logging.info("Hit tasks-io test!")
    return "tasks-io test"
