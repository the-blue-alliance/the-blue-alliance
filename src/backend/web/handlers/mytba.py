import datetime

from werkzeug.wrappers import Response

from backend.common.helpers.season_helper import SeasonHelper
from backend.web.decorators import require_login
from backend.web.profiled_render import render_template


# @require_login
def mytba_live() -> Response:
    year = SeasonHelper.get_current_season()
    now = datetime.datetime.now()

    past_events_with_teams = []
    live_events_with_teams = []
    future_events_with_teams = []

    template_values = {
        "year": year,
        "past_only": year < now.year,
        "past_events_with_teams": past_events_with_teams,
        "live_events_with_teams": live_events_with_teams,
        "future_events_with_teams": future_events_with_teams,
    }

    return render_template("mytba_live.html", template_values)
