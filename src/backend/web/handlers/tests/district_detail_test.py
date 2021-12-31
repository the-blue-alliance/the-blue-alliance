import re
from typing import List

import pytest
from bs4 import BeautifulSoup
from freezegun import freeze_time
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.models.district import District
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.web.handlers.conftest import CapturedTemplate
from backend.web.handlers.tests import helpers


def test_get_bad_district_key(web_client: Client) -> None:
    resp = web_client.get("/events/asdf")
    assert resp.status_code == 404


def test_get_bad_year(ndb_stub, web_client: Client) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/events/ne/2222")
    assert resp.status_code == 404


def test_render_district(ndb_stub, web_client: Client) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200
    assert "max-age=86400" in resp.headers["Cache-Control"]

    soup = BeautifulSoup(resp.data, "html.parser")

    district_name = soup.find(id="district-name")
    assert "".join(district_name.contents) == "2020 NE District"


def test_valid_years_dropdown(ndb_stub, web_client: Client) -> None:
    [helpers.preseed_district(f"{year}ne") for year in range(2014, 2021)]

    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    year_dropdown = BeautifulSoup(resp.data, "html.parser").find(id="valid-years")
    assert year_dropdown is not None

    expected_years = list(reversed(range(2014, 2021)))
    assert [
        int(y.string) for y in year_dropdown.contents if y != "\n"
    ] == expected_years


def test_valid_districts_dropdown(ndb_stub, web_client: Client) -> None:
    [helpers.preseed_district(f"2020{district}") for district in ["ne", "fim", "mar"]]

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


def test_district_detail_render_teams_sorted(ndb_stub, web_client: Client) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    all_teams = helpers.get_all_teams(resp.data)
    assert len(all_teams) == 5

    # Test teams are sorted
    for i in range(1, 4):
        assert all_teams[i].team_number == all_teams[i - 1].team_number + 1


def test_district_detail_team_list_has_expected_data_with_location(
    web_client: Client, ndb_stub
) -> None:
    helpers.preseed_district("2020ne")

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
    web_client: Client, ndb_stub
) -> None:
    helpers.preseed_district("2020ne")

    resp = web_client.get("/events/ne/2020")
    assert resp.status_code == 200

    tables = helpers.find_teams_tables(resp.data)
    assert len(tables) == 2
    teams1 = helpers.get_teams_from_table(tables[0])
    teams2 = helpers.get_teams_from_table(tables[1])

    # We set 5 teams to start, so they should be split 3 and 2
    assert len(teams1) == 3
    assert len(teams2) == 2


def test_district_details_render_events(web_client: Client, ndb_stub) -> None:
    helpers.preseed_district("2020ne")

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


@freeze_time("2019-03-09")
def test_district_details_render_active_teams(
    web_client: Client, ndb_stub, setup_full_event
) -> None:
    helpers.preseed_district("2019ne")
    setup_full_event("2019ctwat")

    # Make sure we have DistrictTeam links for all the teams
    event: Event = none_throws(Event.get_by_id("2019ctwat"))
    district_teams = [
        DistrictTeam(
            id=f"2019ne_{team.key_name}",
            year=2019,
            district_key=ndb.Key(District, "2019ne"),
            team=team.key,
        )
        for team in event.teams
    ]
    ndb.put_multi(district_teams)

    resp = web_client.get("/events/ne/2019")
    assert resp.status_code == 200
    assert "max-age=900" in resp.headers["Cache-Control"]

    soup = BeautifulSoup(resp.data, "html.parser")
    active_teams = soup.find(id="active-teams")
    assert active_teams is not None

    live_teams_table = active_teams.find(id="live-teams")
    assert live_teams_table is not None

    live_teams = live_teams_table.find_all(
        "tr", id=re.compile(r"live-team-2019ctwat-frc\d{3}")
    )
    assert len(live_teams) == 41


@freeze_time("2021-06-01")
@pytest.mark.parametrize(
    "year, expects_rankings, cache_ttl", [(2020, True, 86400), (2021, False, 900)]
)
def test_district_detail_rankings(
    year,
    expects_rankings,
    cache_ttl,
    ndb_stub,
    captured_templates: List[CapturedTemplate],
    web_client: Client,
):
    district_key = f"{year}fim"

    helpers.preseed_district(district_key)

    rankings: List[DistrictRanking] = [
        DistrictRanking(
            rank=1,
            team_key="frc7332",
            point_toal=83,
            rookie_bonus=0,
            event_points=[
                TeamAtEventDistrictPoints(
                    event_key=f"{year}event1",
                    qual_points=22,
                    elim_points=30,
                    alliance_points=16,
                    award_points=15,
                    total=83,
                )
            ],
        ),
    ]

    district = none_throws(District.get_by_id(district_key))
    district.rankings = rankings
    district.put()

    response = web_client.get(f"/events/fim/{year}")

    assert response.status_code == 200
    assert f"max-age={cache_ttl}" in response.headers["Cache-Control"]
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "district_details.html"
    if expects_rankings:
        assert context["rankings"] == rankings
    else:
        assert context["rankings"] is None
