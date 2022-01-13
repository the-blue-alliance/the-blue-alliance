from flask import abort, Blueprint, request, url_for
from flask.helpers import make_response
from google.appengine.api import taskqueue
from werkzeug.wrappers import Response

from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, Year

blueprint = Blueprint("live_events", __name__)


@blueprint.route("/tasks/do/update_live_events")
def update_live_events() -> str:
    FirebasePusher.update_live_events()
    return ""


@blueprint.route("/tasks/math/enqueue/event_team_status/<int:year>")
def enqueue_eventteam_status(year: Year) -> Response:
    """
    Enqueues calculation of event team status for a year
    """
    event_keys = [e.id() for e in Event.query(Event.year == year).fetch(keys_only=True)]
    for event_key in event_keys:
        taskqueue.add(
            url=url_for("live_events.update_event_team_status", event_key=event_key),
            method="GET",
            queue_name="default",
            target="py3-tasks-io",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(f"Enqueued for: {event_keys}")

    return make_response("")


@blueprint.route("/tasks/math/do/event_team_status/<event_key>")
def update_event_team_status(event_key: EventKey) -> Response:
    """
    Calculates event team statuses for all teams at an event
    """
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    event_teams = EventTeam.query(EventTeam.event == event.key).fetch()
    for event_team in event_teams:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            event_team.team.id(), event
        )
        event_team.status = status
        # FirebasePusher.update_event_team_status(event_key, event_team.team.id(), status)
    EventTeamManipulator.createOrUpdate(event_teams)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            f"Finished calculating event team statuses for: {event_key}"
        )
    return make_response("")
