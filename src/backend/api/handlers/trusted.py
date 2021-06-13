from typing import List, Optional

from flask import jsonify, make_response, request, Response
from google.cloud import ndb

from backend.api.api_trusted_parsers.json_match_video_parser import JSONMatchVideoParser
from backend.api.api_trusted_parsers.json_team_list_parser import (
    JSONTeamListParser,
)
from backend.api.handlers.decorators import require_write_auth, validate_event_key
from backend.common.consts.auth_type import AuthType
from backend.common.futures import TypedFuture
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey
from backend.common.models.match import Match
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


@require_write_auth({AuthType.MATCH_VIDEO})
@validate_event_key
def add_match_video(event_key: EventKey) -> Response:
    match_key_to_video = JSONMatchVideoParser.parse(event_key, request.data)
    match_keys = [ndb.Key(Match, k) for k in match_key_to_video.keys()]
    match_futures: List[TypedFuture[Match]] = ndb.get_multi_async(match_keys)

    nonexistent_matches = []
    matches_to_put = []
    for (match_key, youtube_id), match_future in zip(
        match_key_to_video.items(), match_futures
    ):
        match = match_future.get_result()
        if match is None:
            nonexistent_matches.append(match_key)
            continue

        elif youtube_id not in match.youtube_videos:
            match.youtube_videos.append(youtube_id)
            matches_to_put.append(match)

    if nonexistent_matches:
        return make_response(
            jsonify({"Error": f"Matches {nonexistent_matches} do not exist!"}), 404
        )

    if matches_to_put:
        MatchManipulator.createOrUpdate(matches_to_put)

    return jsonify({"Success": "Match videos successfully updated"})
