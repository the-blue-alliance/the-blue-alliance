from flask import Flask
from api.handlers.root import RootHandler
from common.middleware import install_middleware


app = Flask(__name__)
install_middleware(app)

app.add_url_rule("/api/<path:path>", view_func=RootHandler)
