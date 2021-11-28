from typing import List, Optional

from flask import jsonify, make_response, request, Response
from google.appengine.ext import ndb
from google.appengine.ext.deferred import defer
from pyre_extensions import none_throws

from backend.api.api_trusted_parsers.json_alliance_selections_parser import (
    JSONAllianceSelectionsParser,
)
from backend.api.api_trusted_parsers.json_event_info_parser import JSONEventInfoParser
from backend.api.api_trusted_parsers.json_match_video_parser import JSONMatchVideoParser
from backend.api.api_trusted_parsers.json_team_list_parser import (
    JSONTeamListParser,
)
from backend.api.handlers.decorators import require_write_auth, validate_event_key
from backend.common.consts.auth_type import AuthType
from backend.common.futures import TypedFuture
from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.event import EventDetails
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


@require_write_auth({AuthType.EVENT_INFO})
@validate_event_key
def update_event_info(event_key: EventKey) -> Response:
    parsed_info = JSONEventInfoParser.parse(request.data)
    event: Event = none_throws(Event.get_by_id(event_key))

    if "webcasts" in parsed_info:
        EventWebcastAdder.add_webcast(
            event,
            parsed_info["webcasts"],
            False,  # don't createOrUpdate yet
        )

    if "remap_teams" in parsed_info:
        event.remap_teams = parsed_info["remap_teams"]
        defer(EventRemapTeamsHelper.remap_teams, event_key, _queue="admin")

    if "first_event_code" in parsed_info:
        event.official = parsed_info["first_event_code"] is not None
        event.first_code = parsed_info["first_event_code"]

    if "playoff_type" in parsed_info:
        event.playoff_type = parsed_info["playoff_type"]

    EventManipulator.createOrUpdate(event)
    return jsonify({"Success": f"Event {event_key} updated"})


@require_write_auth({AuthType.EVENT_ALLIANCES})
@validate_event_key
def update_event_alliances(event_key: EventKey) -> Response:
    alliance_selections = JSONAllianceSelectionsParser.parse(request.data)
    event: Event = none_throws(Event.get_by_id(event_key))

    event_details = EventDetails(id=event_key, alliance_selections=alliance_selections)

    if event.remap_teams:
        EventRemapTeamsHelper.remapteams_alliances(
            event_details.alliance_selections, event.remap_teams
        )
    EventDetailsManipulator.createOrUpdate(event_details)

    return jsonify({"Success": "Alliance selections successfully updated"})
