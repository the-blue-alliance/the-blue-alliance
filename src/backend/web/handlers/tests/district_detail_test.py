import re

from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client


from backend.web.handlers.tests import helpers


def test_get_bad_district_key(web_client: Client) -> None:
    resp = web_client.get("/events/asdf")
    assert resp.status_code == 404


def test_get_bad_year(ndb_client: ndb.Client, web_client: Client) -> None:
    helpers.preseed_district(ndb_client, "2020ne")
    resp = web_client.get("/events/ne/2222")
    assert resp.status_code == 404


def test_render_district(ndb_client: ndb.Client, web_client: Client) -> None:
    helpers.preseed_district(ndb_client, "2020ne")
    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    district_name = soup.find(id="district-name")
    assert "".join(district_name.contents) == "2020 NE District"


def test_valid_years_dropdown(ndb_client: ndb.Client, web_client: Client) -> None:
    [helpers.preseed_district(ndb_client, f"{year}ne") for year in range(2014, 2021)]

    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    year_dropdown = BeautifulSoup(resp.data, "html.parser").find(id="valid-years")
    assert year_dropdown is not None

    expected_years = list(reversed(range(2014, 2021)))
    assert [
        int(y.string) for y in year_dropdown.contents if y != "\n"
    ] == expected_years


def test_valid_districts_dropdown(ndb_client: ndb.Client, web_client: Client) -> None:
    [
        helpers.preseed_district(ndb_client, f"2020{district}")
        for district in ["ne", "fim", "mar"]
    ]

    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    district_dropdown = BeautifulSoup(resp.data, "html.parser").find(
        id="valid-districts"
    )
    assert district_dropdown is not None

    expected_districts = ["All Events", "FIM", "MAR"]
    assert [
        y.string for y in district_dropdown.contents if y != "\n"
    ] == expected_districts


def test_district_detail_render_teams_sorted(
    ndb_client: ndb.Client, web_client: Client
) -> None:
    helpers.preseed_district(ndb_client, "2020ne")
    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    all_teams = helpers.get_all_teams(resp.data)
    assert len(all_teams) == 5

    # Test teams are sorted
    for i in range(1, 4):
        assert all_teams[i].team_number == all_teams[i - 1].team_number + 1


def test_district_detail_team_list_has_expected_data_with_location(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    helpers.preseed_district(ndb_client, "2020ne")

    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    all_teams = helpers.get_all_teams(resp.data)
    assert len(all_teams) == 5
    for team_number, team in zip(range(1, 6), all_teams):
        assert team == helpers.ParsedTeam(
            team_number=team_number,
            team_number_link=f"/team/{team_number}/2020",
            team_name=f"The {team_number} Team",
            team_name_link=f"/team/{team_number}/2020",
            team_location=f"City {team_number}",
        )


def test_district_detail_team_list_splits_teams_in_half(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    helpers.preseed_district(ndb_client, "2020ne")

    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    tables = helpers.find_teams_tables(resp.data)
    assert len(tables) == 2
    teams1 = helpers.get_teams_from_table(tables[0])
    teams2 = helpers.get_teams_from_table(tables[1])

    # We set 5 teams to start, so they should be split 3 and 2
    assert len(teams1) == 3
    assert len(teams2) == 2


def test_district_details_render_events(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    helpers.preseed_district(ndb_client, "2020ne")

    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    week_labels = BeautifulSoup(resp.data, "html.parser").find_all(
        id=re.compile(r"event_label_container_.*")
    )
    assert len(week_labels) == 4
    assert ["".join(t.find("h2").strings) for t in week_labels] == [
        "Week 1 2 Events",
        "Week 2 1 Events",
        "Week 3 1 Events",
        "Week 4 1 Events",
    ]
