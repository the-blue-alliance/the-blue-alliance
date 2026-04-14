from flask import abort
from google.appengine.api import taskqueue

from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks


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

    # Update the CMP reg hacks sitevar to disable event team fetch for parent event
    reg_sitevar = ChampsRegistrationHacks.get()

    new_divisions_to_skip = list(reg_sitevar["divisions_to_skip"])
    if event_key not in new_divisions_to_skip:
        new_divisions_to_skip.append(event_key)

    new_start_day_to_last = list(reg_sitevar["set_start_to_last_day"])
    if event_key not in new_start_day_to_last:
        new_start_day_to_last.append(event_key)

    ChampsRegistrationHacks.put(
        {
            "divisions_to_skip": new_divisions_to_skip,
            "set_start_to_last_day": new_start_day_to_last,
            "skip_eventteams": reg_sitevar["skip_eventteams"],
            "event_name_override": reg_sitevar["event_name_override"],
        }
    )

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
