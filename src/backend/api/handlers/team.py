from backend.common.decorators import cached_public
from backend.api.handlers.decorators import api_authenticated


@api_authenticated
@cached_public
def team(team_key: str) -> dict:
    return {"team_key": team_key}


@api_authenticated
@cached_public
def team_list(page_num: int) -> dict:
    return {"page_num": page_num}
