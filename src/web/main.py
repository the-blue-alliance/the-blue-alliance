from flask import Flask
from web.handlers import HomeHandler
from web.jinja2_filters import register_template_filters


app = Flask(__name__)
app.add_url_rule("/", view_func=HomeHandler)
register_template_filters(app)
