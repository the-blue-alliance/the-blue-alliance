from flask import jsonify

from backend.api.handlers.decorators import api_authenticated
from backend.common.decorators import cached_public
from backend.common.queries.team_query import TeamQuery, TeamListQuery


@api_authenticated
@cached_public
def team(team_key: str) -> dict:
    return jsonify(TeamQuery(team_key=team_key).fetch_dict(3))


@api_authenticated
@cached_public
def team_list(page_num: int) -> list:
    return jsonify(TeamListQuery(page=page_num).fetch_dict(3))
