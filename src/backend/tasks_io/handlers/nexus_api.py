import json
from typing import List, Optional

from flask import abort, Blueprint, make_response, request, Response, url_for
from google.appengine.api import taskqueue

from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.memcache_models.event_nexus_queue_status_memcache import (
    EventNexusQueueStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, Year
from backend.common.queries.event_query import EventListQuery
from backend.common.queries.team_query import EventEventTeamsQuery
from backend.tasks_io.datafeeds.datafeed_nexus import DatafeedNexus

blueprint = Blueprint("nexus_api", __name__)


@blueprint.route(
    "/tasks/enqueue/nexus_pit_locations/current_year",
    defaults={"year": None, "current_year": True},
)
@blueprint.route(
    "/tasks/enqueue/nexus_pit_locations/now",
    defaults={"year": None, "current_year": False},
)
@blueprint.route(
    "/tasks/enqueue/nexus_pit_locations/<int:year>", defaults={"current_year": False}
)
def enqueue_nexus_pit_locations_current(
    year: Optional[Year], current_year: bool
) -> Response:
    events: List[Event]
    if year is None and not current_year:
        events = EventHelper.events_within_a_day()
    else:
        events = EventListQuery(year=year or SeasonHelper.get_current_season()).fetch()

    events = list(filter(lambda e: e.official, events))

    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("nexus_api.event_pit_locations", event_key=event.key_name),
            method="GET",
        )
    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(f"Enqueued pit updates for {[e.key_name for e in events]}")

    return make_response("")


@blueprint.route("/tasks/get/nexus_pit_locations/<event_key>")
def event_pit_locations(event_key: EventKey) -> Response:
    if not Event.validate_key_name(event_key):
        abort(400)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    nexus_df = DatafeedNexus()
    eventteams_future = EventEventTeamsQuery(event_key).fetch_async()
    nexus_pit_locations_future = nexus_df.get_event_team_pit_locations(event_key)

    eventteams = eventteams_future.get_result()
    nexus_pit_locations = nexus_pit_locations_future.get_result()

    for eventteam in eventteams:
        team_key = eventteam.team.string_id()
        if nexus_pit_locations and team_key in nexus_pit_locations:
            eventteam.pit_location = nexus_pit_locations[team_key]
        else:
            eventteam.pit_location = None

    EventTeamManipulator.createOrUpdate(eventteams)
    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(f"Fetched pit locations: {eventteams}")

    return make_response("")


@blueprint.route("/tasks/enqueue/nexus_queue_status/now")
def current_event_queue_status() -> Response:
    events = EventHelper.events_within_a_day()
    events = list(filter(lambda e: e.official, events))
    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("nexus_api.event_queue_status", event_key=event.key_name),
            method="GET",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            f"Enqueued queue updates for {[e.key_name for e in events]}"
        )

    return make_response("")


@blueprint.route("/tasks/get/nexus_queue_status/<event_key>")
def event_queue_status(event_key: EventKey) -> Response:
    if not Event.validate_key_name(event_key):
        abort(400)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    event.prep_matches()

    nexus_df = DatafeedNexus()
    event_queue_status_future = nexus_df.get_event_queue_status(event)

    event_queue_status = event_queue_status_future.get_result()

    # Write the results to memcache
    mc_model = EventNexusQueueStatusMemcache(event.key_name)
    mc_model.put(event_queue_status)

    # Write the results to firebase
    for match in event.matches:
        FirebasePusher.update_match_queue_status(match, event_queue_status)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            f"Fetched nexus queue data:\n{json.dumps(event_queue_status)}"
        )

    return make_response("")
