import json
from typing import List

from flask import abort, Blueprint, make_response, request, url_for
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.event_type import EventType, SEASON_EVENT_TYPES
from backend.common.futures import TypedFuture
from backend.common.helpers.district_helper import DistrictHelper
from backend.common.helpers.event_helper import EventHelper
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.models.district import District
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import DistrictKey, EventKey, Year
from backend.common.models.team import Team
from backend.common.queries.district_query import DistrictsInYearQuery
from backend.common.queries.event_query import DistrictEventsQuery
from backend.common.queries.team_query import DistrictTeamsQuery


blueprint = Blueprint("math", __name__)


@blueprint.route("/tasks/math/enqueue/district_points_calc/<int:year>")
def enqueue_event_district_points_calc(year: Year) -> Response:
    """
    Enqueues calculation of district points for all season events for a given year
    """
    event_keys: List[ndb.Key] = Event.query(
        Event.year == year, Event.event_type_enum.IN(SEASON_EVENT_TYPES)
    ).fetch(None, keys_only=True)
    for event_key in event_keys:
        taskqueue.add(
            url=url_for(
                "math.event_district_points_calc", event_key=event_key.string_id()
            ),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            "Enqueued for: {}".format([event_key.id() for event_key in event_keys])
        )

    return make_response("")


@blueprint.route("/tasks/math/do/district_points_calc/<event_key>")
def event_district_points_calc(event_key: EventKey) -> Response:
    """
    Calculates district points for an event
    """
    event = Event.get_by_id(event_key)
    if event is None:
        abort(404)

    if event.event_type_enum not in SEASON_EVENT_TYPES and not request.args.get(
        "allow-offseason", None
    ):
        return make_response(
            f"Can't calculate district points for a non-season event {event.key_name}!",
            400,
        )

    district_points = DistrictHelper.calculate_event_points(event)
    event_details = EventDetails(id=event_key, district_points=district_points)
    EventDetailsManipulator.createOrUpdate(event_details)

    # Enqueue task to update rankings
    if event.district_key:
        taskqueue.add(
            url=url_for(
                "math.district_rankings_calc",
                district_key=event.district_key.string_id(),
            ),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(json.dumps(district_points, sort_keys=True, indent=2))

    return make_response("")


@blueprint.route("/tasks/math/enqueue/district_rankings_calc/<int:year>")
def enqueue_district_rankings_calc(year: Year) -> Response:
    """
    Enqueues calculation of rankings for all districts for a given year
    """

    districts = DistrictsInYearQuery(int(year)).fetch()
    district_keys = [district.key.id() for district in districts]
    for district_key in district_keys:
        taskqueue.add(
            url=url_for("math.district_rankings_calc", district_key=district_key),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )
        taskqueue.add(
            url=url_for("frc_api.district_rankings", district_key=district_key),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(f"Enqueued for: {district_keys}")
    return make_response("")


@blueprint.route("/tasks/math/do/district_rankings_calc/<district_key>")
def district_rankings_calc(district_key: DistrictKey) -> Response:
    """
    Calculates district rankings for a district year
    """
    district = District.get_by_id(district_key)
    if not district:
        return make_response(f"District {district_key} not found", 404)

    events_future: TypedFuture[List[Event]] = DistrictEventsQuery(
        district_key
    ).fetch_async()
    teams_future: TypedFuture[List[Team]] = DistrictTeamsQuery(
        district_key
    ).fetch_async()

    events = events_future.get_result()
    for event in events:
        event.prep_details()
    events = EventHelper.sorted_events(events)
    team_totals = DistrictHelper.calculate_rankings(events, teams_future, district.year)

    rankings: List[DistrictRanking] = []
    current_rank = 1
    for key, points in team_totals.items():
        point_detail = DistrictRanking(
            rank=current_rank,
            team_key=key,
            event_points=[],
            rookie_bonus=points.get("rookie_bonus", 0),
            point_total=points["point_total"],
        )
        for event, event_points in points["event_points"]:
            event_points["event_key"] = event.key_name
            event_points["district_cmp"] = (
                event.event_type_enum == EventType.DISTRICT_CMP
                or event.event_type_enum == EventType.DISTRICT_CMP_DIVISION
            )
            point_detail["event_points"].append(event_points)

        rankings.append(point_detail)
        current_rank += 1

    if rankings:
        district.rankings = rankings
        DistrictManipulator.createOrUpdate(district)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(f"Finished calculating rankings for: {district_key}")
    return make_response("")
