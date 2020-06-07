from flask import Flask
from backend.common.middleware import install_middleware
from backend.web.handlers.index import index
from backend.web.handlers.gameday import gameday
from backend.web.handlers.team import team_canonical, team_list
from backend.web.jinja2_filters import register_template_filters


app = Flask(__name__)
install_middleware(app)

app.add_url_rule("/", view_func=index)
app.add_url_rule("/gameday", view_func=gameday)
app.add_url_rule("/team/<int:team_number>", view_func=team_canonical)
app.add_url_rule("/teams/<int:page>", view_func=team_list)
app.add_url_rule("/teams", view_func=team_list, defaults={"page": 1})
register_template_filters(app)
