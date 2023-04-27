import json
import logging
from typing import List, Optional

from flask import abort, Blueprint, make_response, render_template, request, url_for
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.event_type import EventType, SEASON_EVENT_TYPES
from backend.common.futures import TypedFuture
from backend.common.helpers.district_helper import DistrictHelper
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_insights_helper import EventInsightsHelper
from backend.common.helpers.event_team_updater import EventTeamUpdater
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.matchstats_helper import MatchstatsHelper
from backend.common.helpers.prediction_helper import PredictionHelper
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.district import District
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import DistrictKey, EventKey, Year
from backend.common.models.team import Team
from backend.common.queries.district_query import DistrictsInYearQuery
from backend.common.queries.event_query import DistrictEventsQuery, EventListQuery
from backend.common.queries.team_query import DistrictTeamsQuery


blueprint = Blueprint("math", __name__)


@blueprint.route("/backend-tasks-b2/math/enqueue/insights/<type>/<int:year>")
def enqueue_year_insights(type: str, year: Year) -> Response:
    """
    Enqueues Insights calculation of a given kind for a given year
    """
    return make_response("")


@blueprint.route("/backend-tasks-b2/math/do/insights/<type>/<int:year>")
def do_year_insights(type: str, year: Year) -> Response:
    """
    Calculates insights of a given kind for a given year.
    """
    return make_response("")


@blueprint.route("/backend-tasks-b2/math/enqueue/overallinsights/<type>/<int:year>")
def enqueue_overall_insights(type: str, year: Year) -> Response:
    """
    Enqueues Overall Insights calculation for a given kind.
    """
    return make_response("")


@blueprint.route("/backend-tasks-b2/math/do/overallinsights/<type>/<int:year>")
def do_overall_insights(type: str, year: Year) -> Response:
    """
    Calculates overall insights of a given kind.
    """
    return make_response("")
