from flask import Flask

from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware
from backend.tasks_io.handlers.index import index


configure_logging()

app = Flask(__name__)
install_middleware(app, prefix="tasks-io")

app.url_map.strict_slashes = False

app.add_url_rule("/", view_func=index)
