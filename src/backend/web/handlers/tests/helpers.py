import re
from datetime import datetime
from typing import List, NamedTuple, Optional, Tuple

import bs4
from google.cloud import ndb

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamNumber
from backend.common.models.team import Team


class TeamCurrentEvent(NamedTuple):
    event_key: Optional[str]
    webcast: Optional[Tuple[str, str]]  # (link, text)
    currently_competing: Optional[str]
    upcoming_matches: Optional[bool]


class TeamInfo(NamedTuple):
    header: str
    location: Optional[str]
    full_name: Optional[str]
    rookie_year: Optional[str]
    last_competed: Optional[str]
    website: Optional[str]
    home_cmp: Optional[str]
    hof: Optional[str]
    district: Optional[str]
    district_link: Optional[str]
    social_media: Optional[List[Tuple[str, str]]]  # tuple of (slug_name, foreign_key)
    preferred_medias: Optional[
        List[Tuple[str, str]]
    ]  # tuple of (slug_name, foreign_key)
    current_event: Optional[TeamCurrentEvent]


class TeamEventParticipation(NamedTuple):
    event_name: str


class TeamEventHistory(NamedTuple):
    year: int
    event: str
    awards: List[str]


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


def preseed_event(ndb_client: ndb.Client, event_key: EventKey) -> None:
    with ndb_client.context():
        Event(
            id=event_key,
            event_short=event_key[4:],
            year=int(event_key[:4]),
            name="Test Event",
            event_type_enum=EventType.OFFSEASON,
            start_date=datetime(2020, 3, 1),
            end_date=datetime(2020, 3, 5),
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
    header = soup.find(id="team-title")
    location = soup.find(id="team-location")
    full_name = soup.find(id="team-name")
    rookie_year = soup.find(id="team-rookie-year")
    last_competed = soup.find(id="team-last-competed")
    website = soup.find(id="team-website")
    home_cmp = soup.find(id="team-home-cmp")
    hof = soup.find(id="team-hof")
    district = soup.find(id="team-district")
    district = district.find("a") if district else None
    social_media = soup.find(id="team-social-media")
    social_media = (
        [
            (m["data-media-type"], "".join(m.stripped_strings))
            for m in social_media.find_all(attrs={"data-media-type": True})
        ]
        if social_media
        else None
    )
    preferred_carousel = soup.find(id=re.compile(r"team-carousel-frc\d+"))
    preferred_medias = (
        [
            (m["data-media-type"], m["data-foreign-key"])
            for m in preferred_carousel.find_all(attrs={"data-media-type": True})
        ]
        if preferred_carousel
        else None
    )

    current_event = None
    current_soup = soup.find(id="current-event")
    if current_soup:
        current_webcast = current_soup.find(id="current-event-webcast")
        currently_competing = current_soup.find(attrs={"class": "panel-title"})
        upcoming_matches = current_soup.find(attrs={"class": "panel-body"})
        upcoming_match_table = (
            upcoming_matches.find(attrs={"class": "match-table"})
            if upcoming_matches
            else None
        )
        current_event = TeamCurrentEvent(
            event_key=current_soup["data-event-key"],
            webcast=(current_webcast["href"], "".join(current_webcast.stripped_strings))
            if current_webcast
            else None,
            currently_competing="".join(currently_competing.stripped_strings)
            if currently_competing
            else None,
            upcoming_matches=upcoming_match_table is not None,
        )

    return TeamInfo(
        header="".join(header.stripped_strings),
        location=location.string.strip() if location else None,
        full_name=full_name.string.strip() if full_name else None,
        rookie_year=rookie_year.string.strip() if rookie_year else None,
        last_competed=last_competed.string.strip() if last_competed else None,
        website=website.string.strip() if website else None,
        home_cmp=home_cmp.string.strip() if home_cmp else None,
        hof=hof.string.strip() if hof else None,
        district=district.string.strip() if district else None,
        district_link=district["href"] if district else None,
        social_media=social_media or None,
        preferred_medias=preferred_medias or None,
        current_event=current_event,
    )


def get_team_history(resp_data: str) -> Optional[List[TeamEventHistory]]:
    soup = bs4.BeautifulSoup(resp_data, "html.parser")
    history_table = soup.find(id="competition-list-table")
    if not history_table:
        return None

    events = history_table.find("tbody").find_all("tr")
    return [
        TeamEventHistory(
            year=int(e.find_all("td")[0].string),
            event="".join(e.find_all("td")[1].stripped_strings),
            awards=list(e.find_all("td")[2].stripped_strings),
        )
        for e in events
    ]


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
    return TeamEventParticipation(
        event_name=event.find("h3").string.strip(),
    )


def assert_alert(div: bs4.element.Tag, title: str, message: str, success: bool) -> None:
    # Ensure our status alert contains 1) a close button, 2) a h4, 3) a status message
    close_button = div.find(
        "button", attrs={"type": "button", "class": "close", "data-dismiss": "alert"}
    )
    assert close_button
    assert close_button.text.encode("utf-8") == b"\xc3\x97"
    assert ("alert-success" if success else "alert-danger") in div.attrs["class"]
    alert_title = div.find("h4")
    assert alert_title
    assert alert_title.text == title
    alert_message = div.find("p")
    assert alert_message
    assert alert_message.text == message
