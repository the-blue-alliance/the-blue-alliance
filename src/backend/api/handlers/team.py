from typing import Optional

from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated, validate_team_key
from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    filter_team_properties,
    ModelType,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team
from backend.common.queries.district_query import TeamDistrictsQuery
from backend.common.queries.event_query import TeamEventsQuery
from backend.common.queries.media_query import TeamSocialMediaQuery
from backend.common.queries.robot_query import TeamRobotsQuery
from backend.common.queries.team_query import (
    TeamListQuery,
    TeamListYearQuery,
    TeamParticipationQuery,
    TeamQuery,
)


@api_authenticated
@validate_team_key
@cached_public
def team(team_key: TeamKey, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns details about one team, specified by |team_key|.
    """
    track_call_after_response("team", team_key, model_type)

    team = TeamQuery(team_key=team_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        team = filter_team_properties([team], model_type)[0]
    return jsonify(team)


@api_authenticated
@validate_team_key
@cached_public
def team_years_participated(team_key: TeamKey) -> Response:
    """
    Returns a list of years the given Team participated in an event.
    """
    track_call_after_response("team/years_participated", team_key)

    years_participated = TeamParticipationQuery(team_key=team_key).fetch()
    years_participated = sorted(years_participated)
    return jsonify(years_participated)


@api_authenticated
@validate_team_key
@cached_public
def team_history_districts(team_key: TeamKey) -> Response:
    """
    Returns a list of all DistrictTeam models associated with the given Team.
    """
    track_call_after_response("team/history/districts", team_key)

    team_districts = TeamDistrictsQuery(team_key=team_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    return jsonify(team_districts)


@api_authenticated
@validate_team_key
@cached_public
def team_history_robots(team_key: TeamKey) -> Response:
    """
    Returns a list of all Robot models associated with the given Team.
    """
    track_call_after_response("team/history/robots", team_key)

    team_robots = TeamRobotsQuery(team_key=team_key).fetch_dict(ApiMajorVersion.API_V3)
    return jsonify(team_robots)


@api_authenticated
@validate_team_key
@cached_public
def team_social_media(team_key: TeamKey) -> Response:
    """
    Returns a list of all social media models associated with the given Team.
    """
    track_call_after_response("team/social_media", team_key)

    team_social_media = TeamSocialMediaQuery(team_key=team_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    return jsonify(team_social_media)


@api_authenticated
@validate_team_key
@cached_public
def team_events(team_key: TeamKey, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of all event models associated with the given Team.
    """
    track_call_after_response("team/events", team_key, model_type)

    team_events = TeamEventsQuery(team_key=team_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        team_events = filter_event_properties(team_events, model_type)
    return jsonify(team_events)


@api_authenticated
@cached_public
def team_list_all(model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of all teams.
    """
    track_call_after_response("team/list", "all", model_type)

    max_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
    max_team_num = int(max_team_key.id()[3:])
    max_team_page = int(max_team_num / 500)

    futures = []
    for page_num in range(max_team_page + 1):
        futures.append(
            TeamListQuery(page=page_num).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    team_list = []
    for future in futures:
        partial_team_list = future.get_result()
        team_list += partial_team_list

    if model_type is not None:
        team_list = filter_team_properties(team_list, model_type)
    return jsonify(team_list)


@api_authenticated
@cached_public
def team_list(page_num: int, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of teams, paginated by team number in sets of 500.
    page_num = 0 returns teams from 0-499
    page_num = 1 returns teams from 500-999
    page_num = 2 returns teams from 1000-1499
    etc.
    """
    track_call_after_response("team/list", str(page_num), model_type)

    team_list = TeamListQuery(page=page_num).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        team_list = filter_team_properties(team_list, model_type)
    return jsonify(team_list)


@api_authenticated
@cached_public
def team_list_year(
    year: int, page_num: int, model_type: Optional[ModelType] = None
) -> Response:
    """
    Returns a list of teams for a given year, paginated by team number in sets of 500.
    page_num = 0 returns teams from 0-499
    page_num = 1 returns teams from 500-999
    page_num = 2 returns teams from 1000-1499
    etc.
    """
    track_call_after_response(f"team/list/{year}", str(page_num), model_type)

    team_list = TeamListYearQuery(year=year, page=page_num).fetch_dict(
        ApiMajorVersion.API_V3
    )
    if model_type is not None:
        team_list = filter_team_properties(team_list, model_type)
    return jsonify(team_list)
