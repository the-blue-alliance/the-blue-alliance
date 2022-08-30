from datetime import datetime, timedelta

from werkzeug.wrappers import Response

from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.models.event import Event
from backend.web.profiled_render import render_template


@cached_public
def webcast_list() -> Response:
    year = datetime.now().year
    events = Event.query(Event.year == year).order(Event.start_date)

    template_values = {
        "events": events,
        "year": year,
    }

    return make_cached_response(
        render_template("webcasts.html", template_values),
        ttl=timedelta(weeks=1),
    )
