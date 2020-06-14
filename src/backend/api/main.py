from flask import Flask

from backend.api.handlers.root import root
from backend.common.middleware import install_middleware


app = Flask(__name__)
install_middleware(app)

app.add_url_rule("/api/<path:path>", view_func=root)
