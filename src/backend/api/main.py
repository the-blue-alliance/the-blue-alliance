from flask import Flask
from backend.api.handlers.error import handle_404
from backend.api.handlers.team import team, team_list
from backend.common.middleware import install_middleware


app = Flask(__name__)
install_middleware(app)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

app.add_url_rule("/api/v3/team/<team_key>", view_func=team)
app.add_url_rule("/api/v3/teams/<int:page_num>", view_func=team_list)

app.register_error_handler(404, handle_404)
