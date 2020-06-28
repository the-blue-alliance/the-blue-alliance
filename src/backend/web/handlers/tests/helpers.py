from datetime import datetime
from typing import List, NamedTuple, Optional

import bs4
from google.cloud import ndb

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamNumber
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


class TeamEventParticipation(NamedTuple):
    event_name: str


def preseed_team(ndb_client: ndb.Client, team_number: TeamNumber) -> None:
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
    ndb_client: ndb.Client, team_number: TeamNumber, event_key: EventKey
) -> None:
    with ndb_client.context():
        Event(
            id=event_key,
            event_short=event_key[4:],
            year=int(event_key[:4]),
            name="Test Event",
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


def get_page_title(resp_data: str) -> str:
    soup = bs4.BeautifulSoup(resp_data, "html.parser")
    title = soup.find("title")
    return title.string.strip()


def get_years_participated_dropdown(resp_data: str) -> List[str]:
    soup = bs4.BeautifulSoup(resp_data, "html.parser")
    dropdown = soup.find("ul", id="team-year-dropdown")
    print(f"{dropdown.contents}")
    return [li.string.strip() for li in dropdown.contents if li.name == "li"]


def get_team_event_participation(
    resp_data: str, event_key: EventKey
) -> TeamEventParticipation:
    soup = bs4.BeautifulSoup(resp_data, "html.parser")
    event = soup.find(id=event_key)
    return TeamEventParticipation(event_name=event.find("h3").string.strip(),)
