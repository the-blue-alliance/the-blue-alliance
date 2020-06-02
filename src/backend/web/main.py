from flask import Flask
from backend.common.middleware import install_middleware
from backend.web.handlers.index import index
from backend.web.handlers.gameday import gameday
from backend.web.jinja2_filters import register_template_filters


app = Flask(__name__)
install_middleware(app)

app.add_url_rule("/", view_func=index)
app.add_url_rule("/gameday", view_func=gameday)
register_template_filters(app)
