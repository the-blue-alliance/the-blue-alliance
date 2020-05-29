from flask import Flask
from web.handlers import RootHandler


app = Flask(__name__)
app.add_url_rule("/", view_func=RootHandler)
