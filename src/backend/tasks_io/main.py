from flask import Flask
from google.appengine.api import wrap_wsgi_app

from backend.common.logging import configure_logging
from backend.common.middleware import install_middleware


configure_logging()

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app, use_deferred=True)
install_middleware(app)
