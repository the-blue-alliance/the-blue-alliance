from typing import Any, cast, Dict

from flask import abort
from google.appengine.api import taskqueue

from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event, EventSyncOverrides
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey


def admin_clear_eventteams(event_key: EventKey) -> str:
    if not Event.validate_key_name(event_key):
        abort(400)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    existing_event_team_keys = set(
        EventTeam.query(EventTeam.event == event.key).fetch(1000, keys_only=True)
    )
    EventTeamManipulator.delete_keys(existing_event_team_keys)

    return f"Deleted {len(existing_event_team_keys)} EventTeams from {event_key}"


def admin_post_division_tasks(event_key: EventKey) -> str:
    if not Event.validate_key_name(event_key):
        abort(400)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    sync_overrides = cast(
        EventSyncOverrides,
        dict(cast(Dict[str, Any], event.sync_overrides or {})),
    )
    sync_overrides["skip_eventteams"] = True
    sync_overrides["set_start_day_to_last"] = True
    event.sync_overrides = sync_overrides
    EventManipulator.createOrUpdate(event)

    # Delete event teams from the parent event
    existing_event_team_keys_query = EventTeam.query(EventTeam.event == event.key)
    existing_event_team_keys = set()
    cursor = None
    more = True
    while more:
        keys, cursor, more = existing_event_team_keys_query.fetch_page(
            1000, start_cursor=cursor, keys_only=True
        )
        existing_event_team_keys.update(keys)
    EventTeamManipulator.delete_keys(existing_event_team_keys)

    # Re-enqueue event details fetch for the parent event
    taskqueue.add(
        queue_name="datafeed",
        target="py3-tasks-io",
        url=f"/backend-tasks/get/event_details/{event_key}",
        method="GET",
    )

    return f"post_division_tasks complete for {event_key}"
