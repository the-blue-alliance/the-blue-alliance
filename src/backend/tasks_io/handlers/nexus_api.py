from flask import abort, Blueprint, make_response, request, Response, url_for
from google.appengine.api import taskqueue

from backend.common.helpers.event_helper import EventHelper
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.queries.team_query import EventEventTeamsQuery
from backend.tasks_io.datafeeds.datafeed_nexus import DatafeedNexus

blueprint = Blueprint("nexus_api", __name__)


@blueprint.route("/tasks/enqueue/nexus_pit_locations/now")
def enqueue_nexus_pit_locations_current() -> Response:
    events = EventHelper.events_within_a_day()
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
