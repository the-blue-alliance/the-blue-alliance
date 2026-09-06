import json

from bs4 import BeautifulSoup
from werkzeug.test import Client

from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team


def _preseed_thread(team_number: int, nickname: str | None) -> None:
    team_key = Team(
        id=f"frc{team_number}",
        team_number=team_number,
        nickname=nickname,
    ).put()
    Media(
        id=f"cd-thread-team-{team_number}",
        media_type_enum=MediaType.CD_THREAD,
        foreign_key=f"team-{team_number}",
        year=2020,
        references=[team_key],
        details_json=json.dumps({"thread_title": f"Team {team_number} thread"}),
    ).put()


def test_team_number_link_includes_nickname_tooltip(
    ndb_stub, web_client: Client
) -> None:
    _preseed_thread(254, "The Cheesy Poofs")

    response = web_client.get("/team-threads/2020")

    assert response.status_code == 200
    team_link = BeautifulSoup(response.data, "html.parser").find(
        "a", href="/team/254/2020"
    )
    assert team_link is not None
    assert team_link["rel"] == ["tooltip"]
    assert team_link["title"] == "The Cheesy Poofs"


def test_team_number_link_omits_empty_tooltip(ndb_stub, web_client: Client) -> None:
    _preseed_thread(254, None)

    response = web_client.get("/team-threads/2020")

    assert response.status_code == 200
    team_link = BeautifulSoup(response.data, "html.parser").find(
        "a", href="/team/254/2020"
    )
    assert team_link is not None
    assert "rel" not in team_link.attrs
    assert "title" not in team_link.attrs
