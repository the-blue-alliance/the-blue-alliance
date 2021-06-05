from typing import List, Optional

from flask import jsonify, request, Response
from google.cloud import ndb

from backend.api.api_trusted_parsers.json_team_list_parser import (
    JSONTeamListParser,
)
from backend.api.handlers.decorators import require_write_auth, validate_event_key
from backend.common.consts.auth_type import AuthType
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey
from backend.common.models.team import Team


@require_write_auth({AuthType.EVENT_TEAMS})
@validate_event_key
def update_teams(event_key: EventKey) -> Response:
    team_key_names = JSONTeamListParser.parse(request.data)
    team_keys = [ndb.Key(Team, key_name) for key_name in team_key_names]

    teams: List[Optional[Team]] = ndb.get_multi(team_keys)
    old_eventteam_keys_future = EventTeam.query(
        EventTeam.event == ndb.Key(Event, event_key)
    ).fetch_async(None, keys_only=True)

    event_teams: List[EventTeam] = []
    for team in teams:
        # Only create EventTeam objects for Teams that exist
        if team:
            event_teams.append(
                EventTeam(
                    id=f"{event_key}_{team.key_name}",
                    event=ndb.Key(Event, event_key),
                    team=team.key,
                    year=int(event_key[:4]),
                )
            )

    # Delete old EventTeams
    old_eventteam_keys: List[ndb.Key] = old_eventteam_keys_future.get_result()
    to_delete = set(old_eventteam_keys).difference(set([et.key for et in event_teams]))
    if to_delete:
        EventTeamManipulator.delete_keys(to_delete)

    # Write new EventTeams
    if event_teams:
        EventTeamManipulator.createOrUpdate(event_teams)

    return jsonify({"Success": "Event teams successfully updated"})
