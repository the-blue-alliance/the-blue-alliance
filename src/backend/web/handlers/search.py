from datetime import timedelta

from flask import redirect, request, url_for
from werkzeug import Response

from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.web.profiled_render import render_template


@cached_public(ttl=timedelta(days=1))
def search_handler() -> Response:
    q = request.args.get("q", "")

    # if team number
    if q.isdigit():
        team_key = f"frc{q}"
        team = Team.get_by_id(team_key)
        if team is not None:
            return redirect(url_for("team_canonical", team_number=int(q)))
    # if team key
    elif Team.validate_key_name(q):
        team = Team.get_by_id(q)
        if team is not None:
            return redirect(url_for("team_canonical", team_number=int(q[3:])))

    # if event key
    elif Event.validate_key_name(q):
        event = Event.get_by_id(q)
        if event is not None:
            return redirect(url_for("event_detail", event_key=q))

    # if valid event short for the current year
    else:
        current_season = SeasonHelper.get_current_season()
        event_key = f"{current_season}{q}"
        if (
            Event.validate_key_name(event_key)
            and Event.get_by_id(event_key) is not None
        ):
            return redirect(url_for("event_detail", event_key=event_key))

    return render_template("search.html")
