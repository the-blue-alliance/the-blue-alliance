import datetime
import json
import logging
from typing import Dict, List, Optional

import pytz
from flask import abort, Blueprint, request, url_for
from flask.helpers import make_response
from google.appengine.api import taskqueue
from werkzeug.wrappers import Response

from backend.common.consts.nexus_match_status import NexusMatchStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.match_time_prediction_helper import (
    MatchTimePredictionHelper,
)
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.memcache_models.district_webcast_last_updated_memcache import (
    DistrictWebcastLastUpdatedData,
    DistrictWebcastLastUpdatedMemcache,
)
from backend.common.memcache_models.event_nexus_queue_status_memcache import (
    EventNexusQueueStatusMemcache,
)
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_playoff_advancement import EventPlayoffAdvancement
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, EventKey, Year
from backend.common.models.match import Match
from backend.common.models.webcast import Webcast
from backend.common.queries.event_query import DistrictEventsQuery
from backend.common.queries.match_query import EventMatchesQuery
from backend.common.sitevars.apistatus_down_events import ApiStatusDownEvents
from backend.tasks_io.helpers.live_event_helper import LiveEventHelper
from backend.tasks_io.helpers.webcast_online_helper import WebcastOnlineHelper

blueprint = Blueprint("live_events", __name__)


def _has_unplayed_match_today(event: Event) -> bool:
    """Return True if the event has at least one unplayed match scheduled for today."""
    local_today = event.local_time().date()
    for match in event.matches:
        if not match.has_been_played and match.time is not None:
            if event.timezone_id:
                match_local_date = (
                    pytz.utc.localize(match.time)
                    .astimezone(pytz.timezone(event.timezone_id))
                    .date()
                )
            else:
                match_local_date = match.time.date()
            if match_local_date == local_today:
                return True
    return False


@blueprint.route("/tasks/do/update_live_events")
def update_live_events() -> str:
    week_events = EventHelper.week_events()
    events, special_webcasts = LiveEventHelper.get_live_events_with_current_webcasts(
        week_events
    )
    FirebasePusher.update_live_events(events, special_webcasts)

    # Try to find webcasts for events that don't have webcasts yet
    # Regionals (and some districts that use webcast units) will publish
    # their webcast info in advance. However, other districts will not.
    # Here, we will try to find their upcoming streams
    districts_to_find = set()
    district_webcast_last_updated_memcache = DistrictWebcastLastUpdatedMemcache()
    cached_last_updated = district_webcast_last_updated_memcache.get()
    district_last_updated: Dict[DistrictKey, int] = {}
    if cached_last_updated is not None:
        district_last_updated = dict(cached_last_updated["district_last_updated"])

    current_time = datetime.datetime.now(tz=pytz.utc)
    throttle_interval = datetime.timedelta(hours=1)
    districts_with_youtube_channels = {
        district.key_name
        for district in District.query(
            District.year == datetime.datetime.now().year
        ).fetch(200)
        if any(
            channel.get("type") == WebcastType.YOUTUBE
            and bool(channel.get("channel_id"))
            for channel in (district.webcast_channels or [])
        )
    }
    for event in week_events:
        if (
            event.now
            and (event_district_key := event.event_district_key)
            and event_district_key in districts_with_youtube_channels
            and not event.current_webcasts
            and _has_unplayed_match_today(event)
        ):
            districts_to_find.add(event_district_key)

    did_enqueue = False
    if districts_to_find:
        for district_key in districts_to_find:
            last_updated = district_last_updated.get(district_key)
            if last_updated is not None:
                elapsed = current_time - datetime.datetime.fromtimestamp(
                    last_updated, tz=pytz.utc
                )
                if elapsed <= throttle_interval:
                    continue

            taskqueue.add(
                url=url_for(
                    "live_events.find_event_webcasts", district_key=district_key
                ),
                method="GET",
                queue_name="default",
                target="py3-tasks-io",
            )
            district_last_updated[district_key] = int(current_time.timestamp())
            did_enqueue = True

    if did_enqueue:
        district_webcast_last_updated_memcache.put(
            DistrictWebcastLastUpdatedData(district_last_updated=district_last_updated)
        )

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
    nexus_queue_info = EventNexusQueueStatusMemcache(event_key).get()
    if (
        nexus_queue_info
        and played_matches
        and (most_recent_match := played_matches[-1])
        and (nexus_match := nexus_queue_info["matches"].get(most_recent_match.key_name))
        and nexus_match["status"] != NexusMatchStatus.ON_FIELD
    ):
        # If the most recent match isnt' set to "on field", then we assume
        # the data is stale, or there is an issue, so do not use the data
        nexus_queue_info = None

    MatchTimePredictionHelper.predict_future_matches(
        event_key,
        played_matches,
        unplayed_matches,
        timezone,
        event.within_a_day,
        nexus_queue_info,
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
    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return f"Predicted match times for {len(unplayed_matches)} matches\n{[m.key_name + " " + m.predicted_time.isoformat() for m in unplayed_matches if m.predicted_time is not None]}"

    return ""


@blueprint.route("/tasks/do/update_webcast_online_status/<event_key>")
def update_event_webcast_status(event_key: EventKey) -> Response:
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    WebcastOnlineHelper.add_online_status(event.webcast)
    return make_response(f"Updated event webcasts: {event.webcast}")


@blueprint.route("/tasks/do/find_event_webcasts/<district_key>")
def find_event_webcasts(district_key: DistrictKey) -> Response:
    district = District.get_by_id(district_key)
    if district is None:
        abort(400)

    youtube_channel_ids = [
        channel["channel_id"]
        for channel in (district.webcast_channels or [])
        if channel.get("type") == WebcastType.YOUTUBE
        and channel.get("channel_id")
    ]
    if not youtube_channel_ids:
        abort(400)

    # Fetch district events and upcoming streams from all channels in parallel
    district_events_future = DistrictEventsQuery(district_key).fetch_async()
    upcoming_streams_futures = [
        YouTubeVideoHelper.get_upcoming_streams(channel_id)
        for channel_id in youtube_channel_ids
    ]

    district_events = district_events_future.get_result()
    upcoming_streams = [
        stream for future in upcoming_streams_futures for stream in future.get_result()
    ]

    future_events_without_webcasts = [
        event
        for event in district_events
        if event.within_a_day and not event.current_webcasts
    ]
    event_to_streams: Dict[str, List] = {}
    for stream in upcoming_streams:
        matched_events = [
            e
            for e in future_events_without_webcasts
            if e.short_name and e.short_name in stream["title"]
        ]
        if len(matched_events) == 0:
            logging.info(f"Did not find an event match for stream {stream}")
            continue
        if len(matched_events) > 1:
            # If there are multiple matched events, we can't be sure which one it is, so skip
            logging.info(
                f"Multiple matched events for stream {stream['stream_id']}: {[e.key_name for e in matched_events]}"
            )
            continue

        event_key = matched_events[0].key_name
        if event_key not in event_to_streams:
            event_to_streams[event_key] = []
        event_to_streams[event_key].append((matched_events[0], stream))

    discovered_webcasts: List[str] = []
    for event_key, event_stream_pairs in event_to_streams.items():
        streams = [stream for _, stream in event_stream_pairs]
        event = event_stream_pairs[0][0]
        # Fetch start times for all streams in parallel
        start_time_futures = [
            YouTubeVideoHelper.get_scheduled_start_time(stream["stream_id"])
            for stream in streams
        ]
        start_times = [future.get_result() for future in start_time_futures]

        for stream, start_time in zip(streams, start_times):
            if not start_time:
                logging.info(f"Could not find start time for stream {stream}, skipping")
                continue

            new_webcast = Webcast(
                type=WebcastType.YOUTUBE,
                channel=stream["stream_id"],
                date=start_time,
            )

            EventWebcastAdder.add_webcast(event, new_webcast)
            discovered_webcasts.append(
                f"{event.key_name}: {stream['stream_id']} ({start_time})"
            )

    if "X-Appengine-Taskname" not in request.headers:
        if discovered_webcasts:
            discovered_webcasts_str = "\n".join(discovered_webcasts)
            return make_response(f"Discovered webcasts:\n{discovered_webcasts_str}")
        return make_response("Discovered webcasts: none")

    return make_response("")


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
