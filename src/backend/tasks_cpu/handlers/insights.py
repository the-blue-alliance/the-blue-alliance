import logging
from html import escape
from typing import Optional

from flask import abort, Blueprint, make_response, render_template, request, url_for
from google.appengine.api import taskqueue
from werkzeug.wrappers import Response

from backend.common.consts.insight_type import InsightType
from backend.common.helpers.insights_helper import InsightsHelper
from backend.common.helpers.insights_leaderboard_event_helper import (
    InsightsLeaderboardEventHelper,
)
from backend.common.helpers.insights_leaderboard_match_helper import (
    InsightsLeaderboardMatchHelper,
)
from backend.common.helpers.insights_leaderboard_team_helper import (
    InsightsLeaderboardTeamHelper,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.insight_manipulator import InsightManipulator
from backend.common.models.insight import Insight, LeaderboardKeyType
from backend.common.models.keys import Year


blueprint = Blueprint("insights", __name__)


@blueprint.route("/backend-tasks-b2/math/enqueue/insights/<kind>/<int:year>")
@blueprint.route(
    "/backend-tasks-b2/math/enqueue/insights/<kind>", defaults={"year": None}
)
def enqueue_year_insights(kind: str, year: Optional[Year] = None) -> Response:
    if year is None:
        year = SeasonHelper.get_current_season()

    """
    Enqueues Insights calculation of a given kind for a given year
    """
    try:
        insight_type = InsightType(kind)
        taskqueue.add(
            url=url_for("insights.do_year_insights", kind=insight_type, year=year),
            method="GET",
            target="py3-tasks-cpu",
            queue_name="default",
        )
    except ValueError:
        logging.warning(f"Unknown insight kind {kind}")
        abort(404)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("math/year_insights_enqueue.html", kind=kind, year=year)
        )

    return make_response("")


@blueprint.route("/backend-tasks-b2/math/do/insights/<kind>/<int:year>")
def do_year_insights(kind: str, year: Year) -> Response:
    """
    Calculates insights of a given kind for a given year.
    """
    insights = None
    insight_kind = None

    try:
        insight_kind = InsightType(kind)
    except ValueError:
        logging.warning(f"Unknown insight kind {kind}")
        abort(404)

    if insight_kind == InsightType.MATCHES:
        insights = InsightsHelper.doMatchInsights(year)
    elif insight_kind == InsightType.AWARDS:
        insights = InsightsHelper.doAwardInsights(year)
    elif insight_kind == InsightType.PREDICTIONS:
        insights = InsightsHelper.doPredictionInsights(year)

    if insights is not None:
        InsightManipulator.createOrUpdate(insights)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("math/year_insights_do.html", kind=kind, insights=insights)
        )

    return make_response("")


@blueprint.route("/backend-tasks-b2/math/do/insights/leaderboards/<kind>/<int:year>")
def do_leaderboard_year_insights(kind: LeaderboardKeyType, year: Year) -> Response:
    if kind not in Insight.TYPED_LEADERBOARD_KEY_TYPES.values():
        return make_response(f"Unknown leaderboard kind {escape(kind)}")

    insights = []
    if kind == "match":
        insights = InsightsLeaderboardMatchHelper.make_insights(year)
    elif kind == "team":
        insights = InsightsLeaderboardTeamHelper.make_insights(year)
    elif kind == "event":
        insights = InsightsLeaderboardEventHelper.make_insights(year)

    if len(insights) > 0:
        InsightManipulator.createOrUpdate(insights)

    return make_response(repr(insights))


@blueprint.route(
    "/backend-tasks-b2/math/enqueue/insights/leaderboards/<kind>/<int:year>"
)
@blueprint.route(
    "/backend-tasks-b2/math/enqueue/insights/leaderboards/<kind>",
    defaults={"year": None},
)
def enqueue_leaderboard_year_insights(
    kind: LeaderboardKeyType, year: Optional[Year] = None
) -> Response:
    if year is None:
        year = SeasonHelper.get_current_season()

    taskqueue.add(
        url=url_for("insights.do_leaderboard_year_insights", kind=kind, year=year),
        method="GET",
        target="py3-tasks-cpu",
        queue_name="default",
    )

    return make_response(
        f"enqueued {escape(kind)} leaderboard insights for year {escape(str(year))}"
    )


@blueprint.route("/backend-tasks-b2/math/enqueue/insights/leaderboards/<kind>/all")
def enqueue_all_leaderboard_insights(kind: LeaderboardKeyType) -> Response:
    for year in SeasonHelper.get_valid_years():
        taskqueue.add(
            url=url_for("insights.do_leaderboard_year_insights", kind=kind, year=year),
            method="GET",
            target="py3-tasks-cpu",
            queue_name="default",
        )

    return make_response(f"enqueued {escape(kind)} leaderboard insights for all years")


@blueprint.route("/backend-tasks-b2/math/enqueue/overallinsights/<kind>")
def enqueue_overall_insights(kind: str) -> Response:
    """
    Enqueues Overall Insights calculation for a given kind.
    """
    taskqueue.add(
        url=url_for("insights.do_overall_insights", kind=kind),
        method="GET",
        target="py3-tasks-cpu",
        queue_name="default",
    )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("math/overall_insights_enqueue.html", kind=kind)
        )

    return make_response("")


@blueprint.route("/backend-tasks-b2/math/do/overallinsights/<kind>")
def do_overall_insights(kind: str) -> Response:
    """
    Calculates overall insights of a given kind.
    """
    insights = None
    if kind == "matches":
        insights = InsightsHelper.doOverallMatchInsights()
    elif kind == "awards":
        insights = InsightsHelper.doOverallAwardInsights()

    if insights is not None:
        InsightManipulator.createOrUpdate(insights)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "math/overall_insights_do.html", kind=kind, insights=insights
            )
        )

    return make_response("")


@blueprint.route("/backend-tasks-b2/math/enqueue/insights/<kind>/all")
def enqueue_all_insights_of_kind(kind: str) -> Response:
    """
    Enqueues all insights (all valid years) of a given kind.
    """
    try:
        insight_type = InsightType(kind)
    except ValueError:
        logging.warning(f"Unknown insight kind {kind}")
        abort(404)
        return  # no-op due to abort; only for type-hinting on insight_type

    for year in SeasonHelper.get_valid_years():
        taskqueue.add(
            url=url_for("insights.do_year_insights", kind=insight_type, year=year),
            method="GET",
            target="py3-tasks-cpu",
            queue_name="run-in-order",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("math/all_insights_enqueue.html", kind=kind)
        )

    return make_response("")
