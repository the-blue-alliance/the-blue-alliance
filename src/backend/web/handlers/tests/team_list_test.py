import re
from typing import List, NamedTuple, Optional

import bs4
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.models.team import Team


class ParsedTeam(NamedTuple):
    team_number: int
    team_number_link: Optional[str]
    team_name: str
    team_name_link: Optional[str]
    team_location: str


def preseed_teams(
    ndb_client: ndb.Client, start_team: int, end_team: int, set_city: bool = False
) -> None:
    with ndb_client.context():
        stored = ndb.put_multi(
            [
                Team(
                    id=f"frc{i}",
                    team_number=i,
                    nickname=f"Team {i}",
                    city=f"City {i}" if set_city else None,
                )
                for i in range(start_team, end_team + 1)
            ]
        )
        assert len(stored) == (end_team - start_team + 1)


def find_teams_tables(resp_data: str) -> List[bs4.element.Tag]:
    soup = BeautifulSoup(resp_data, "html.parser")
    return soup.find_all(id=re.compile(r"^teams_[ab]$"))


def get_teams_from_table(table: bs4.element.Tag) -> List[ParsedTeam]:
    team_rows = table.find("tbody").find_all("tr")
    parsed_teams = []
    for t in team_rows:
        team_number = t.find(id=re.compile(r"^team-\d+-number"))
        team_name = t.find(id=re.compile(r"^team-\d+-name"))
        team_location = t.find(id=re.compile(r"^team-\d+-location"))
        parsed_teams.append(
            ParsedTeam(
                team_number=int(team_number.string),
                team_number_link=team_number.get("href"),
                team_name=team_name.string,
                team_name_link=team_name.get("href"),
                team_location=team_location.string,
            )
        )
    return parsed_teams


def get_all_teams(resp_data: str) -> List[ParsedTeam]:
    tables = find_teams_tables(resp_data)
    if len(tables) == 0:
        return []
    assert len(tables) == 2
    return get_teams_from_table(tables[0]) + get_teams_from_table(tables[1])


def test_bad_page(web_client: Client) -> None:
    resp = web_client.get("/teams/9999")
    assert resp.status_code == 404


def test_team_list_empty_no_page(web_client: Client) -> None:
    resp = web_client.get("/teams")
    assert resp.status_code == 200

    assert len(get_all_teams(resp.data)) == 0


def test_team_page_1_redirects(web_client: Client) -> None:
    resp = web_client.get("/teams/1")
    assert resp.status_code == 308
    assert resp.headers["Location"].endswith("/teams")


def test_team_list_empty_with_page(web_client: Client) -> None:
    resp = web_client.get("/teams/2")
    assert resp.status_code == 200

    assert len(get_all_teams(resp.data)) == 0


def test_team_list_sorted_by_team_num(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    preseed_teams(ndb_client, 1, 5)

    resp = web_client.get("/teams")
    assert resp.status_code == 200

    all_teams = get_all_teams(resp.data)
    assert len(all_teams) == 5
    for i in range(1, 5):
        assert all_teams[i].team_number == all_teams[i - 1].team_number + 1


def test_team_list_has_expected_data_no_location(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    preseed_teams(ndb_client, 1, 5)

    resp = web_client.get("/teams")
    assert resp.status_code == 200

    all_teams = get_all_teams(resp.data)
    assert len(all_teams) == 5
    for team_number, team in zip(range(1, 6), all_teams):
        assert team == ParsedTeam(
            team_number=team_number,
            team_number_link=f"/team/{team_number}",
            team_name=f"Team {team_number}",
            team_name_link=f"/team/{team_number}",
            team_location="--",
        )


def test_team_list_has_expected_data_with_location(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    preseed_teams(ndb_client, 1, 5, set_city=True)

    resp = web_client.get("/teams")
    assert resp.status_code == 200

    all_teams = get_all_teams(resp.data)
    assert len(all_teams) == 5
    for team_number, team in zip(range(1, 6), all_teams):
        assert team == ParsedTeam(
            team_number=team_number,
            team_number_link=f"/team/{team_number}",
            team_name=f"Team {team_number}",
            team_name_link=f"/team/{team_number}",
            team_location=f"City {team_number}",
        )


def test_team_list_splits_teams_in_half(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    preseed_teams(ndb_client, 1, 5)

    resp = web_client.get("/teams")
    assert resp.status_code == 200

    tables = find_teams_tables(resp.data)
    assert len(tables) == 2
    teams1 = get_teams_from_table(tables[0])
    teams2 = get_teams_from_table(tables[1])

    # We set 5 teams to start, so they should be split 3 and 2
    assert len(teams1) == 3
    assert len(teams2) == 2


def test_team_list_fetches_offset_from_page_no_data(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    preseed_teams(ndb_client, 1, 5)

    resp = web_client.get("/teams/2")
    assert resp.status_code == 200

    all_teams = get_all_teams(resp.data)
    assert len(all_teams) == 0


def test_team_list_fetches_offset_from_page_with_data(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    # We should query for the [1000, 1004] slice
    preseed_teams(ndb_client, 999, 1004)

    resp = web_client.get("/teams/2")
    assert resp.status_code == 200

    all_teams = get_all_teams(resp.data)
    assert len(all_teams) == 5
    for team_number, team in zip(range(1000, 1005), all_teams):
        assert team == ParsedTeam(
            team_number=team_number,
            team_number_link=f"/team/{team_number}",
            team_name=f"Team {team_number}",
            team_name_link=f"/team/{team_number}",
            team_location="--",
        )
