from datetime import timedelta

from werkzeug.wrappers import Response

from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.queries.event_query import EventListQuery
from backend.web.profiled_render import render_template


@cached_public
def webcast_list() -> Response:
    year = SeasonHelper.get_current_season()
    events = EventListQuery(year).fetch()
    sorted_events = EventHelper.sorted_events(events)

    template_values = {
        "events": sorted_events,
        "year": year,
    }

    return make_cached_response(
        render_template("webcasts.html", template_values),
        ttl=timedelta(weeks=1),
    )
