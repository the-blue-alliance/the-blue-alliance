from flask import abort
from werkzeug.wrappers import Response

from backend.common.decorators import cached_public
from backend.common.models.event import Event
from backend.common.models.keys import MatchKey
from backend.common.models.match import Match
from backend.web.profiled_render import render_template


@cached_public
def match_detail(match_key: MatchKey) -> Response:
    match_future = Match.get_by_id_async(match_key)
    event_future = Event.get_by_id_async(match_key.split("_")[0])
    match = match_future.get_result()
    event = event_future.get_result()

    if not match:
        abort(404)

    """
    zebra_data = ZebraMotionWorks.get_by_id(match_key)
    gdcv_data = MatchGdcvDataQuery(match_key).fetch()
    timeseries_data = None
    if gdcv_data and len(gdcv_data) >= 147 and len(gdcv_data) <= 150:  # Santiy checks on data
        timeseries_data = json.dumps(gdcv_data)
    """

    match_breakdown_template = None
    if match.score_breakdown is not None and match.year >= 2015:
        match_breakdown_template = (
            "match_partials/match_breakdown/match_breakdown_{}.html".format(match.year)
        )

    template_values = {
        "event": event,
        "match": match,
        "match_breakdown_template": match_breakdown_template,
        "timeseries_data": None,  # timeseries_data,
        "zebra_data": None,  # json.dumps(zebra_data.data) if zebra_data else None,
    }

    return render_template("match_details.html", template_values)
