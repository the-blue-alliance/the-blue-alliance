from backend.api.flask_decorators import api_authenticated


@api_authenticated
def team(team_key: str) -> dict:
    return {"team_key": team_key}


@api_authenticated
def team_list(page_num: int) -> dict:
    return {"page_num": page_num}
