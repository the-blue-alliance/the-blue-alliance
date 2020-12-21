from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated, validate_team_key
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.models.keys import TeamKey
from backend.common.queries.team_query import TeamListQuery, TeamQuery


@validate_team_key
@api_authenticated
@cached_public
def team(team_key: TeamKey) -> Response:
    return jsonify(TeamQuery(team_key=team_key).fetch_dict(ApiMajorVersion.API_V3))


@api_authenticated
@cached_public
def team_list(page_num: int) -> Response:
    return jsonify(TeamListQuery(page=page_num).fetch_dict(ApiMajorVersion.API_V3))
