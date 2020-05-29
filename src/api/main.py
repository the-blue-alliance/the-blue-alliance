from flask import Flask
from api.handlers import RootHandler


app = Flask(__name__)
app.add_url_rule("/api/<path:path>", view_func=RootHandler)
