import pytest
from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_helper_utils import LeaderboardInsightArguments
from backend.common.helpers.insights_notable_helper import InsightsNotableHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team


@pytest.fixture(autouse=True)
def setup(ndb_stub):
    Event(
        id="2024mil",
        year=2024,
        event_short="mil",
        event_type_enum=EventType.CMP_DIVISION,
    ).put()
    Team(id="frc2713", team_number=2713).put()
    Award(
        id="2024mil_1",
        year=2024,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.CMP_DIVISION,
        event=ndb.Key(Event, "2024mil"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc604")],
    ).put()
    Award(
        id="2024mil_2",
        year=2024,
        award_type_enum=AwardType.FINALIST,
        event_type_enum=EventType.CMP_DIVISION,
        event=ndb.Key(Event, "2024mil"),
        name_str="Finalist",
        team_list=[ndb.Key(Team, "frc2713")],
    ).put()
    Event(
        id="2024new",
        year=2024,
        event_short="new",
        event_type_enum=EventType.CMP_DIVISION,
    ).put()
    Award(
        id="2024new_1",
        year=2024,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.CMP_DIVISION,
        event=ndb.Key(Event, "2024new"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc1323")],
    ).put()
    Event(
        id="2024cmptx",
        year=2024,
        event_short="cmptx",
        event_type_enum=EventType.CMP_FINALS,
    ).put()
    Award(
        id="2024cmptx_1",
        year=2024,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.CMP_FINALS,
        event=ndb.Key(Event, "2024cmptx"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc2791")],
    ).put()
    Award(
        id="2024cmptx_2",
        year=2024,
        award_type_enum=AwardType.CHAIRMANS,
        event_type_enum=EventType.CMP_FINALS,
        event=ndb.Key(Event, "2024cmptx"),
        name_str="Chairman's Award",
        team_list=[ndb.Key(Team, "frc5254")],
    ).put()


def test_notables_hall_of_fame(ndb_stub):
    insight = InsightsNotableHelper._calculate_notables_hall_of_fame(
        LeaderboardInsightArguments(
            events=[Event.get_by_id("2024cmptx")],
            year=2024,
        )
    )

    assert insight is not None
    assert insight.data["entries"] == [
        {"team_key": "frc5254", "context": ["2024cmptx"]}
    ]


def test_notables_world_champions(ndb_stub):
    insight = InsightsNotableHelper._calculate_notables_world_champions(
        LeaderboardInsightArguments(
            events=[Event.get_by_id("2024cmptx")],
            year=2024,
        )
    )

    assert insight is not None
    assert insight.data["entries"] == [
        {"team_key": "frc2791", "context": ["2024cmptx"]}
    ]


def test_notables_division_winners(ndb_stub):
    insight = InsightsNotableHelper._calculate_notables_division_winners(
        LeaderboardInsightArguments(
            events=[
                Event.get_by_id("2024cmptx"),
                Event.get_by_id("2024new"),
                Event.get_by_id("2024mil"),
            ],
            year=2024,
        )
    )

    assert insight is not None
    assert insight.data["entries"] == [
        {"team_key": "frc1323", "context": ["2024new"]},
        {"team_key": "frc604", "context": ["2024mil"]},
    ]


def test_notables_division_finals_appearances(ndb_stub):
    insight = InsightsNotableHelper._calculate_notables_division_finals_appearances(
        LeaderboardInsightArguments(
            events=[
                Event.get_by_id("2024cmptx"),
                Event.get_by_id("2024new"),
                Event.get_by_id("2024mil"),
            ],
            year=2024,
        )
    )

    assert insight is not None
    assert insight.data["entries"] == [
        {"team_key": "frc1323", "context": ["2024new"]},
        {"team_key": "frc604", "context": ["2024mil"]},
        {"team_key": "frc2713", "context": ["2024mil"]},
    ]


def test_notables_dcmp_winner(ndb_stub):
    # Set up DCMPs
    events = []
    for event_short, years in [
        ("necmp", [2018, 2019, 2020, 2021, 2022]),
        ("micmp", [2018, 2019, 2020, 2021, 2022]),
    ]:
        for year in years:
            Event(
                id=f"{year}{event_short}",
                year=year,
                event_short=event_short,
                event_type_enum=EventType.DISTRICT_CMP,
            ).put()
            events.append(Event.get_by_id(f"{year}{event_short}"))

            Award(
                id=f"{year}{event_short}_winner",
                year=year,
                award_type_enum=AwardType.WINNER,
                event_type_enum=EventType.DISTRICT_CMP,
                event=ndb.Key(Event, f"{year}{event_short}"),
                name_str="Winner",
                team_list=[
                    ndb.Key(Team, "frc2713" if event_short == "necmp" else "frc1")
                ],
            ).put()

            # Set up divisions to make sure we don't count them
            for div in range(1, 3):
                Event(
                    id=f"{year}{event_short}{div}",
                    year=year,
                    event_short=f"{event_short}{div}",
                    event_type_enum=EventType.DISTRICT_CMP_DIVISION,
                ).put()
                events.append(Event.get_by_id(f"{year}{event_short}{div}"))

                Award(
                    id=f"{year}{event_short}{div}_winner",
                    year=year,
                    award_type_enum=AwardType.WINNER,
                    event_type_enum=EventType.DISTRICT_CMP_DIVISION,
                    event=ndb.Key(Event, f"{year}{event_short}{div}"),
                    name_str="Winner",
                    team_list=[
                        ndb.Key(Team, "frc2713" if event_short == "necmp" else "frc1")
                    ],
                ).put()

    insight = InsightsNotableHelper._calculate_notables_dcmp_winner(
        LeaderboardInsightArguments(
            events=events,
            year=2024,
        )
    )

    assert insight is not None
    assert insight.data["entries"] == [
        {
            "team_key": "frc2713",
            "context": [
                "2018necmp",
                "2019necmp",
                "2020necmp",
                "2021necmp",
                "2022necmp",
            ],
        },
        {
            "team_key": "frc1",
            "context": [
                "2018micmp",
                "2019micmp",
                "2020micmp",
                "2021micmp",
                "2022micmp",
            ],
        },
    ]
