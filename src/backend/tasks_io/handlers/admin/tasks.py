from flask import abort

from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event
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
