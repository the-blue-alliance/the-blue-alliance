from typing import Optional

from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated, validate_team_key
from backend.api.handlers.helpers.model_properties import (
    filter_team_properties,
    ModelType,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team
from backend.common.queries.team_query import (
    TeamListQuery,
    TeamListYearQuery,
    TeamQuery,
)


@validate_team_key
@api_authenticated
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
