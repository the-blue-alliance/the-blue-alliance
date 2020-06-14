from datetime import datetime
from typing import NamedTuple, Optional

import bs4
from freezegun import freeze_time
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


class TeamInfo(NamedTuple):
    header: str
    location: Optional[str]
    full_name: Optional[str]
    rookie_year: Optional[str]
    last_competed: Optional[str]
    website: Optional[str]
    home_cmp: Optional[str]
    hof: Optional[str]


def preseed_team(ndb_client: ndb.Client, team_number: int) -> None:
    with ndb_client.context():
        Team(
            id=f"frc{team_number}",
            team_number=team_number,
            nickname=f"The {team_number} Team",
            name="The Blue Alliance / Some High School",
            city="New York",
            state_prov="NY",
            country="USA",
            website="https://www.thebluealliance.com",
            rookie_year=2008,
        ).put()


def preseed_event_for_team(
    ndb_client: ndb.Client, team_number: int, event_key: str
) -> None:
    with ndb_client.context():
        Event(
            id=event_key,
            event_short=event_key[4:],
            year=int(event_key[:4]),
            event_type_enum=EventType.REGIONAL,
            start_date=datetime(2020, 3, 1),
            end_date=datetime(2020, 3, 5),
        ).put()
        EventTeam(
            id=f"{event_key}_frc{team_number}",
            event=ndb.Key(Event, event_key),
            team=ndb.Key(Team, f"frc{team_number}"),
            year=int(event_key[:4]),
        ).put()


def get_team_info(resp_data: str) -> TeamInfo:
    soup = bs4.BeautifulSoup(resp_data, "html.parser")
    header = soup.find("h2")
    location = soup.find(id="team-location")
    full_name = soup.find(id="team-name")
    rookie_year = soup.find(id="team-rookie-year")
    last_competed = soup.find(id="team-last-competed")
    website = soup.find(id="team-website")
    home_cmp = soup.find(id="team-home-cmp")
    hof = soup.find(id="team-hof")

    return TeamInfo(
        header=header.string.strip(),
        location=location.string.strip() if location else None,
        full_name=full_name.string.strip() if full_name else None,
        rookie_year=rookie_year.string.strip() if rookie_year else None,
        last_competed=last_competed.string.strip() if last_competed else None,
        website=website.string.strip() if website else None,
        home_cmp=home_cmp.string.strip() if home_cmp else None,
        hof=hof.string.strip() if hof else None,
    )


def test_canonical_get_bad_team_num(web_client: Client) -> None:
    resp = web_client.get("/team/0")
    assert resp.status_code == 404


def test_detail_get_bad_team_num(web_client: Client) -> None:
    resp = web_client.get("/team/0/2020")
    assert resp.status_code == 404


def test_canonical_team_not_found(web_client: Client) -> None:
    resp = web_client.get("/team/254")
    assert resp.status_code == 404


def test_detail_team_not_found(web_client: Client) -> None:
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 404


def test_canonical_team_found_no_events(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    preseed_team(ndb_client, 254)
    resp = web_client.get("/team/254")
    # This should render team history, but it's not implemented yet
    assert resp.status_code == 501


def test_detail_team_found_no_events(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    preseed_team(ndb_client, 254)
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200


@freeze_time("2020-02-01")
def test_canonical_team_info(web_client: Client, ndb_client: ndb.Client) -> None:
    preseed_team(ndb_client, 254)
    # We need an event to not render the history page
    preseed_event_for_team(ndb_client, 254, "2020test")
    resp = web_client.get("/team/254")
    assert resp.status_code == 200

    team_info = get_team_info(resp.data)
    assert team_info.header == "Team 254 - The 254 Team"
    assert team_info.location == "New York, NY, USA"
    assert team_info.full_name == "The Blue Alliance / Some High School"
    assert team_info.rookie_year == "Rookie Year: 2008"


def test_detail_team_info(web_client: Client, ndb_client: ndb.Client) -> None:
    preseed_team(ndb_client, 254)
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200

    team_info = get_team_info(resp.data)
    assert team_info.header == "Team 254 - The 254 Team"
    assert team_info.location == "New York, NY, USA"
    assert team_info.full_name == "The Blue Alliance / Some High School"
    assert team_info.rookie_year == "Rookie Year: 2008"
