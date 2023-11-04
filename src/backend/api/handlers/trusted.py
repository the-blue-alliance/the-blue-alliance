import json
import logging
from typing import List, Optional, Set

from flask import make_response, request, Response
from google.appengine.ext import ndb
from google.appengine.ext.deferred import defer
from pyre_extensions import none_throws, safe_json

from backend.api.api_trusted_parsers.json_alliance_selections_parser import (
    JSONAllianceSelectionsParser,
)
from backend.api.api_trusted_parsers.json_awards_parser import JSONAwardsParser
from backend.api.api_trusted_parsers.json_event_info_parser import JSONEventInfoParser
from backend.api.api_trusted_parsers.json_match_video_parser import JSONMatchVideoParser
from backend.api.api_trusted_parsers.json_matches_parser import JSONMatchesParser
from backend.api.api_trusted_parsers.json_rankings_parser import JSONRankingsParser
from backend.api.api_trusted_parsers.json_team_list_parser import (
    JSONTeamListParser,
)
from backend.api.api_trusted_parsers.json_zebra_motionworks_parser import (
    JSONZebraMotionWorksParser,
)
from backend.api.handlers.decorators import require_write_auth, validate_keys
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.auth_type import AuthType
from backend.common.consts.media_type import MediaType
from backend.common.futures import TypedFuture
from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.helpers.match_helper import MatchHelper
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.models.zebra_motionworks import ZebraMotionWorks


@require_write_auth({AuthType.EVENT_TEAMS})
@validate_keys
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

    return profiled_jsonify({"Success": "Event teams successfully updated"})


@require_write_auth({AuthType.MATCH_VIDEO})
@validate_keys
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
            profiled_jsonify({"Error": f"Matches {nonexistent_matches} do not exist!"}),
            404,
        )

    if matches_to_put:
        MatchManipulator.createOrUpdate(matches_to_put)

    return profiled_jsonify({"Success": "Match videos successfully updated"})


@require_write_auth({AuthType.EVENT_INFO})
@validate_keys
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

    EventManipulator.createOrUpdate(event, auto_union=False)
    return profiled_jsonify({"Success": f"Event {event_key} updated"})


@require_write_auth({AuthType.EVENT_ALLIANCES})
@validate_keys
def update_event_alliances(event_key: EventKey) -> Response:
    alliance_selections = JSONAllianceSelectionsParser.parse(request.data)
    event: Event = none_throws(Event.get_by_id(event_key))

    event_details = EventDetails(id=event_key, alliance_selections=alliance_selections)

    if event.remap_teams:
        EventRemapTeamsHelper.remapteams_alliances(
            event_details.alliance_selections, event.remap_teams
        )
    EventDetailsManipulator.createOrUpdate(event_details)

    return profiled_jsonify({"Success": "Alliance selections successfully updated"})


@require_write_auth({AuthType.EVENT_AWARDS})
@validate_keys
def update_event_awards(event_key: EventKey) -> Response:
    awards = JSONAwardsParser.parse(request.data, event_key)
    event: Event = none_throws(Event.get_by_id(event_key))

    awards_to_put: List[Award] = []
    for award in awards:
        awards_to_put.append(
            Award(
                id=Award.render_key_name(event.key_name, award["award_type_enum"]),
                name_str=award["name_str"],
                award_type_enum=award["award_type_enum"],
                year=event.year,
                event=event.key,
                event_type_enum=event.event_type_enum,
                team_list=[
                    ndb.Key(Team, team_key) for team_key in award["team_key_list"]
                ],
                recipient_json_list=[json.dumps(a) for a in award["recipient_list"]],
            )
        )

    # it's easier to clear all awards and add new ones than try to find the difference
    old_award_keys = Award.query(Award.event == event.key).fetch(keys_only=True)
    AwardManipulator.delete_keys(old_award_keys)

    if event.remap_teams:
        EventRemapTeamsHelper.remapteams_awards(awards_to_put, event.remap_teams)
    AwardManipulator.createOrUpdate(awards_to_put)

    return profiled_jsonify({"Success": "Awards successfully updated"})


@require_write_auth({AuthType.EVENT_MATCHES})
@validate_keys
def update_event_matches(event_key: EventKey) -> Response:
    event: Event = none_throws(Event.get_by_id(event_key))
    parsed_matches = JSONMatchesParser.parse(request.data, event.year)

    matches: List[Match] = []
    needs_time: List[Match] = []
    for match in parsed_matches:
        match = Match(
            id=Match.render_key_name(
                event.key_name,
                match["comp_level"],
                match["set_number"],
                match["match_number"],
            ),
            event=event.key,
            year=event.year,
            set_number=match["set_number"],
            match_number=match["match_number"],
            comp_level=match["comp_level"],
            team_key_names=match["team_key_names"],
            alliances_json=match["alliances_json"],
            score_breakdown_json=match["score_breakdown_json"],
            time_string=match["time_string"],
            time=match["time"],
            display_name=match["display_name"],
        )

        if (not match.time or match.time == "") and match.time_string:
            # We can calculate the real time from the time string
            needs_time.append(match)
        matches.append(match)

    if needs_time:
        try:
            MatchHelper.add_match_times(event, needs_time)
        except Exception:
            logging.exception("Failed to calculate match times")

    if event.remap_teams:
        EventRemapTeamsHelper.remapteams_matches(matches, event.remap_teams)
    MatchManipulator.createOrUpdate(matches)

    return profiled_jsonify({"Success": "Matches successfully updated"})


@require_write_auth({AuthType.EVENT_MATCHES})
@validate_keys
def delete_event_matches(event_key: EventKey) -> Response:
    keys_to_delete: Set[ndb.Key] = set()
    try:
        match_keys = safe_json.loads(request.data, List[str])
    except Exception:
        return make_response(
            profiled_jsonify({"Error": "'keys_to_delete' could not be parsed"}), 400
        )

    for match_key in match_keys:
        key_name = f"{event_key}_{match_key}"
        if Match.validate_key_name(key_name):
            keys_to_delete.add(ndb.Key(Match, key_name))

    MatchManipulator.delete_keys(keys_to_delete)

    return profiled_jsonify(
        {
            "keys_deleted": [
                none_throws(key.string_id()).split("_")[1] for key in keys_to_delete
            ]
        }
    )


@require_write_auth({AuthType.EVENT_MATCHES})
@validate_keys
def delete_all_event_matches(event_key: EventKey) -> Response:
    if request.data.decode() != event_key:
        return make_response(
            profiled_jsonify(
                {
                    "Error": "To delete all matches for this event, the body of the request must be the event key."
                }
            ),
            400,
        )

    keys_to_delete = Match.query(Match.event == ndb.Key(Event, event_key)).fetch(
        keys_only=True
    )
    MatchManipulator.delete_keys(keys_to_delete)

    return profiled_jsonify({"Success": "All matches for {} deleted".format(event_key)})


@require_write_auth({AuthType.EVENT_RANKINGS})
@validate_keys
def update_event_rankings(event_key: EventKey) -> Response:
    event: Event = none_throws(Event.get_by_id(event_key))
    rankings = JSONRankingsParser.parse(event.year, request.data)

    event_details = EventDetails(id=event_key, rankings2=rankings)

    if event.remap_teams:
        EventRemapTeamsHelper.remapteams_rankings2(
            event_details.rankings2, event.remap_teams
        )

    EventDetailsManipulator.createOrUpdate(event_details)

    return profiled_jsonify({"Success": "Rankings successfully updated"})


@require_write_auth({AuthType.MATCH_VIDEO})
@validate_keys
def add_event_media(event_key: EventKey) -> Response:
    event: Event = none_throws(Event.get_by_id(event_key))

    video_list = safe_json.loads(request.data, List[str])
    media_to_put: List[Media] = []
    event_reference = Media.create_reference("event", event.key_name)
    for youtube_id in video_list:
        media = Media(
            id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, youtube_id),
            foreign_key=youtube_id,
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            details_json=None,
            private_details_json=None,
            year=event.year,
            references=[event_reference],
            preferred_references=[],
        )
        media_to_put.append(media)

    MediaManipulator.createOrUpdate(media_to_put)
    return profiled_jsonify({"Success": "Media successfully added"})


@require_write_auth({AuthType.ZEBRA_MOTIONWORKS})
@validate_keys
def add_match_zebra_motionworks_info(event_key: EventKey) -> Response:
    to_put: List[ZebraMotionWorks] = []
    for zebra_data in JSONZebraMotionWorksParser.parse(request.data):
        match_key = zebra_data["key"]

        # Check that match_key matches event_key
        if match_key.split("_")[0] != event_key:
            return make_response(
                profiled_jsonify(
                    {
                        "Error": f"Match key {match_key} does not match Event key {event_key}!"
                    }
                ),
                400,
            )

        # Check that match exists
        match: Optional[Match] = Match.get_by_id(match_key)
        if match is None:
            return make_response(
                profiled_jsonify({"Error": f"Match {match_key} does not exist!"}), 400
            )

        # Check that teams in Zebra data and teams in Match differ by at most one team on each alliance.
        for color in ALLIANCE_COLORS:
            match_teams = match.alliances[AllianceColor(color)]["teams"]
            zebra_teams = [
                team["team_key"]
                for team in zebra_data["alliances"][color]  # pyre-ignore
            ]
            if len(set(match_teams).difference(set(zebra_teams))) > 1:
                return make_response(
                    profiled_jsonify(
                        {"Error": f"Match {match_key} teams are not valid!"}
                    ),
                    400,
                )

        to_put.append(
            ZebraMotionWorks(
                id=match_key, event=ndb.Key(Event, event_key), data=zebra_data
            )
        )

    ndb.put_multi(to_put)
    return profiled_jsonify({"Success": "Media successfully added"})
