import json

import pytest
from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_helper import InsightsHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.team import Team


@pytest.fixture(autouse=True)
def setup(ndb_stub):
    # Setup event 1
    Event(
        id="2024camb",
        year=2024,
        event_short="mil",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Team(id="frc604", team_number=604).put()
    Team(id="frc1323", team_number=1323).put()
    Award(
        id="2024camb_1",
        year=2024,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2024camb"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc604"), ndb.Key(Team, "frc1323")],
    ).put()
    Award(
        id="2024camb_2",
        year=2024,
        award_type_enum=AwardType.WOODIE_FLOWERS,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2024camb"),
        name_str="Woodie Flowers",
        team_list=[ndb.Key(Team, "frc604")],
    ).put()
    Award(
        id="2024camb_3",
        year=2024,
        award_type_enum=AwardType.INNOVATION_IN_CONTROL,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2024camb"),
        name_str="Innovation in Control",
        team_list=[ndb.Key(Team, "frc604")],
    ).put()

    # Setup event 2
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

    # Setup event 3
    Event(
        id="2022carv",
        year=2022,
        event_short="carv",
        event_type_enum=EventType.CMP_DIVISION,
    ).put()
    Award(
        id="2022carv_1",
        year=2022,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.CMP_DIVISION,
        event=ndb.Key(Event, "2022carv"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc604"), ndb.Key(Team, "frc1323")],
    ).put()

    # Setup event 4
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

    yield


def test_division_winner_notables_single_year(ndb_stub):
    award_futures = ndb.get_multi_async(
        Award.query(Award.year == 2024).fetch_async(10000, keys_only=True).get_result()
    )
    insights = (
        InsightsHelper._calculate_notables_division_winners_and_finals_appearances(
            award_futures, 2024
        )
    )
    assert len(insights) == 2
    div_winner_insight = next(
        filter(
            lambda x: x.name
            == Insight.INSIGHT_NAMES[Insight.TYPED_NOTABLES_DIVISION_WINNERS],
            insights,
        )
    )

    assert div_winner_insight.year == 2024
    assert div_winner_insight.data_json == json.dumps(
        {
            "entries": [
                {"team_key": "frc604", "context": ["2024mil"]},
                {"team_key": "frc1323", "context": ["2024new"]},
            ]
        }
    )


def test_division_finals_appearances_notables_single_year(ndb_stub):
    award_futures = ndb.get_multi_async(
        Award.query(Award.year == 2024).fetch_async(10000, keys_only=True).get_result()
    )
    insights = (
        InsightsHelper._calculate_notables_division_winners_and_finals_appearances(
            award_futures, 2024
        )
    )
    assert len(insights) == 2
    div_finals_insight = next(
        filter(
            lambda x: x.name
            == Insight.INSIGHT_NAMES[
                Insight.TYPED_NOTABLES_DIVISION_FINALS_APPEARANCES
            ],
            insights,
        )
    )

    assert div_finals_insight.year == 2024
    assert div_finals_insight.data_json == json.dumps(
        {
            "entries": [
                {"team_key": "frc604", "context": ["2024mil"]},
                {"team_key": "frc2713", "context": ["2024mil"]},
                {"team_key": "frc1323", "context": ["2024new"]},
            ]
        }
    )


def test_division_winner_notables_overall(ndb_stub):
    for y in [2022, 2024]:
        for i in InsightsHelper.doAwardInsights(y):
            i.put()

    insights = InsightsHelper.doOverallAwardInsights()
    assert len(insights) == 9
    div_winner_notables = next(
        filter(
            lambda x: x.name
            == Insight.INSIGHT_NAMES[Insight.TYPED_NOTABLES_DIVISION_WINNERS],
            insights,
        )
    )
    assert div_winner_notables is not None
    assert div_winner_notables.year == 0
    assert div_winner_notables.data_json == json.dumps(
        {
            "entries": [
                {"team_key": "frc604", "context": ["2022carv", "2024mil"]},
                {"team_key": "frc1323", "context": ["2022carv", "2024new"]},
            ]
        }
    )
