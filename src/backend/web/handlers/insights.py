from datetime import timedelta

from flask import abort
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.insight import Insight
from backend.web.profiled_render import render_template


@cached_public
def insights_overview() -> Response:
    valid_years = list(reversed(SeasonHelper.get_valid_years()))

    template_values = {
        "valid_years": valid_years,
    }

    insights = ndb.get_multi(
        [
            ndb.Key(Insight, Insight.render_key_name(0, insight_name, None))
            for insight_name in Insight.INSIGHT_NAMES.values()
        ]
    )
    last_updated = None
    for insight in insights:
        if insight:
            template_values[insight.name] = insight
            if last_updated is None:
                last_updated = insight.updated
            else:
                last_updated = max(last_updated, insight.updated)
    template_values["last_updated"] = last_updated

    return make_cached_response(
        render_template("insights.html", template_values),
        ttl=timedelta(minutes=60),
    )


@cached_public
def insights_detail(year: int) -> Response:
    valid_years = list(reversed(SeasonHelper.get_valid_years()))
    if year not in valid_years:
        abort(404)

    template_values = {
        "valid_years": valid_years,
        "selected_year": year,
        "year_specific_insights_template": "event_partials/event_insights_{}.html".format(
            year
        ),
    }

    insights = ndb.get_multi(
        [
            ndb.Key(Insight, Insight.render_key_name(year, insight_name, None))
            for insight_name in Insight.INSIGHT_NAMES.values()
        ]
    )
    last_updated = None
    for insight in insights:
        if insight:
            template_values[insight.name] = insight
            if last_updated is None:
                last_updated = insight.updated
            else:
                last_updated = max(last_updated, insight.updated)
    template_values["last_updated"] = last_updated

    return make_cached_response(
        render_template("insights_details.html", template_values),
        ttl=timedelta(minutes=60),
    )
