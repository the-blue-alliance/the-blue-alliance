import datetime
import json
from typing import List, Optional

import pytz
from flask import abort, Blueprint, request, url_for
from flask.helpers import make_response
from google.appengine.api import taskqueue
from werkzeug.wrappers import Response

from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.match_time_prediction_helper import (
    MatchTimePredictionHelper,
)
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_playoff_advancement import EventPlayoffAdvancement
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, Year
from backend.common.models.match import Match
from backend.common.queries.match_query import EventMatchesQuery
from backend.common.sitevars.apistatus_down_events import ApiStatusDownEvents

blueprint = Blueprint("live_events", __name__)


@blueprint.route("/tasks/do/update_live_events")
def update_live_events() -> str:
    FirebasePusher.update_live_events()
    return ""


@blueprint.route("/tasks/math/enqueue/event_team_status/all", defaults={"year": None})
@blueprint.route("/tasks/math/enqueue/event_team_status/<int:year>")
def enqueue_eventteam_status(year: Optional[Year]) -> Response:
    """
    Enqueues calculation of event team status for a year
    """
    if year is None:
        for season_year in SeasonHelper.get_valid_years():
            taskqueue.add(
                url=url_for("live_events.enqueue_eventteam_status", year=season_year),
                method="GET",
                queue_name="default",
                target="py3-tasks-io",
            )
        return make_response(
            f"enqueued team@event status computation for {SeasonHelper.get_valid_years()}"
        )
    else:
        event_keys = [
            e.id() for e in Event.query(Event.year == year).fetch(keys_only=True)
        ]
        for event_key in event_keys:
            taskqueue.add(
                url=url_for(
                    "live_events.update_event_team_status", event_key=event_key
                ),
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


@blueprint.route(
    "/tasks/math/enqueue/playoff_advancement_update/all", defaults={"year": None}
)
@blueprint.route("/tasks/math/enqueue/playoff_advancement_update/<int:year>")
def enqueue_playoff_advancement_year(year: Optional[Year]) -> Response:
    if year is None:
        for season_year in SeasonHelper.get_valid_years():
            taskqueue.add(
                url=url_for(
                    "live_events.enqueue_playoff_advancement_year", year=season_year
                ),
                method="GET",
            )
        return make_response(
            f"enqueued playoff advancement computation for {SeasonHelper.get_valid_years()}"
        )
    else:
        event_keys = Event.query(Event.year == year).fetch(1000, keys_only=True)
        for event_key in event_keys:
            taskqueue.add(
                url=url_for(
                    "live_events.update_playoff_advancement",
                    event_key=event_key.string_id(),
                ),
                method="GET",
            )
        if (
            "X-Appengine-Taskname" not in request.headers
        ):  # Only write out if not in taskqueue
            return make_response(
                f"enqueued playoff advancement computation for {event_keys}"
            )
        else:
            return make_response("")


@blueprint.route("/tasks/math/enqueue/playoff_advancement_update/<event_key>")
def enqueue_playoff_advancement_update(event_key: EventKey) -> str:
    """
    Enqueue rebuilding playoff advancement details for an event
    """
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    taskqueue.add(
        url=url_for("live_events.update_playoff_advancement", event_key=event.key_name),
        method="GET",
        queue_name="default",
        target="py3-tasks-io",
    )

    return f"Enqueued playoff advancement calc for {event.key_name}"


@blueprint.route("/tasks/math/do/playoff_advancement_update/<event_key>")
def update_playoff_advancement(event_key: EventKey) -> str:
    """
    Rebuilds playoff advancement for a given event
    """
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    matches_future = EventMatchesQuery(event_key).fetch_async()
    matches: List[Match] = matches_future.get_result()

    cleaned_matches, _ = MatchHelper.delete_invalid_matches(matches, event)

    _, org_matches = MatchHelper.organized_matches(cleaned_matches)
    (
        bracket_table,
        playoff_advancement,
        _,
        _,
    ) = PlayoffAdvancementHelper.generate_playoff_advancement(event, org_matches)

    event_details = EventDetails(
        id=event.key_name,
        playoff_advancement=EventPlayoffAdvancement(
            advancement=playoff_advancement,
            bracket=bracket_table,
        ),
    )
    EventDetailsManipulator.createOrUpdate(event_details)

    return f"New playoff advancement for {event.key_name}\n{json.dumps(event_details.playoff_advancement, indent=2, sort_keys=True)}"


@blueprint.route("/tasks/math/enqueue/predict_match_times")
def enqueue_match_time_predictions() -> str:
    """
    Enqueue match time predictions for all current events
    """
    live_events = EventHelper.events_within_a_day()
    for event in live_events:
        taskqueue.add(
            url=url_for(
                "live_events.update_match_time_predictions", event_key=event.key_name
            ),
            method="GET",
            queue_name="default",
            target="py3-tasks-io",
        )
    # taskqueue.add(url='/tasks/do/bluezone_update', method='GET')

    # Clear down events for events that aren't live
    down_events = ApiStatusDownEvents.get()
    live_event_keys = set([e.key.id() for e in live_events])

    old_status = set(down_events)
    new_status = old_status.copy()
    for event_key in old_status:
        if event_key not in live_event_keys:
            new_status.remove(event_key)

    ApiStatusDownEvents.put(list(new_status))

    # Clear API Response cache
    # ApiStatusController.clear_cache_if_needed(old_status, new_status)

    return f"Enqueued time prediction for {len(live_events)} events"


@blueprint.route("/tasks/math/do/predict_match_times/<event_key>")
def update_match_time_predictions(event_key: EventKey) -> str:
    """
    Predicts match times for a given live event
    Also handles detection for whether the event is down
    """
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    matches = event.matches
    if not matches or not event.timezone_id:
        return ""

    timezone: datetime.tzinfo = pytz.timezone(event.timezone_id)
    played_matches = MatchHelper.recent_matches(matches, num=0)
    unplayed_matches = MatchHelper.upcoming_matches(matches, num=len(matches))
    MatchTimePredictionHelper.predict_future_matches(
        event_key, played_matches, unplayed_matches, timezone, event.within_a_day
    )

    # Detect whether the event is down
    # An event NOT down if ANY unplayed match's predicted time is within its scheduled time by a threshold and
    # the last played match (if it exists) wasn't too long ago.
    event_down = len(unplayed_matches) > 0
    for unplayed_match in unplayed_matches:
        if (
            unplayed_match.predicted_time
            and unplayed_match.time
            and unplayed_match.predicted_time
            < unplayed_match.time + datetime.timedelta(minutes=30)
        ) or (
            played_matches == []
            or played_matches[-1].actual_time is None
            or played_matches[-1].actual_time
            > datetime.datetime.now() - datetime.timedelta(minutes=30)
        ):
            event_down = False
            break

    old_status = ApiStatusDownEvents.get()
    new_status = set(old_status.copy())
    if event_down:
        new_status.add(event_key)
    elif event_key in new_status:
        new_status.remove(event_key)

    ApiStatusDownEvents.put(list(new_status))

    # Clear API Response cache
    # ApiStatusController.clear_cache_if_needed(old_status, new_status)
    return ""


@blueprint.route("/tasks/do/update_firebase_event/<event_key>")
def update_firebase_event(event_key: EventKey) -> Response:
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    FirebasePusher.update_live_event(event)
    return make_response("")


@blueprint.route("/tasks/do/update_firebase_matches/<event_key>")
def update_firebase_matches(event_key: EventKey) -> Response:
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    event.prep_matches()

    for match in event.matches:
        FirebasePusher.update_match(match, updated_attrs=set())

    return make_response("")
