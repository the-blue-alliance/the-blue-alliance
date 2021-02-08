from datetime import datetime
from typing import List

from google.cloud import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.model_type import ModelType
from backend.common.helpers.mytba import MyTBA
from backend.common.models.event import Event
from backend.common.models.favorite import Favorite
from backend.common.models.match import Match
from backend.common.models.mytba import MyTBAModel
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team


def _create_one_of_each_mytba_model() -> List[MyTBAModel]:
    e1 = Event(
        id="2020miket",
        year=2020,
        event_short="miket",
        event_type_enum=EventType.DISTRICT,
    )
    e1.put()
    e2 = Event(
        id="2020mitry",
        year=2020,
        event_short="mitry",
        event_type_enum=EventType.DISTRICT,
    )
    e2.put()
    ef = Favorite(model_key=e1.key.string_id(), model_type=ModelType.EVENT)
    es = Subscription(model_key=e2.key.string_id(), model_type=ModelType.EVENT)

    team1 = Team(id="frc1", team_number=1)
    team1.put()
    team2 = Team(id="frc2", team_number=2)
    team2.put()

    tf = Favorite(model_key=team1.key.string_id(), model_type=ModelType.TEAM)
    ts = Subscription(model_key=team2.key.string_id(), model_type=ModelType.TEAM)

    m1 = Match(
        id="2020miket_qm1",
        event=e1.key,
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json="",
    )
    m1.put()
    m2 = Match(
        id="2020miket_qm2",
        event=e1.key,
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=2,
        alliances_json="",
    )
    m2.put()
    mf = Favorite(model_key=m1.key.string_id(), model_type=ModelType.MATCH)
    ms = Subscription(model_key=m2.key.string_id(), model_type=ModelType.MATCH)

    return [ef, es, tf, ts, mf, ms]


def test_event_models() -> None:
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)
    event_models = mytba.event_models

    assert len(event_models) == 2
    assert all([model.model_type == ModelType.EVENT for model in event_models])


def test_events() -> None:
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)

    events = mytba.events

    assert len(events) == 2
    assert all([type(event) is Event for event in events])
    assert {event.key.id() for event in events} == {"2020miket", "2020mitry"}


def test_events_wildcard() -> None:
    wildcard = Subscription(model_key="2019*", model_type=ModelType.EVENT)
    mytba = MyTBA([wildcard])

    events = mytba.events
    assert len(events) == 1

    wildcard_event = events.pop()
    assert wildcard_event.key.id() == "2019*"
    assert wildcard_event.short_name == "ALL EVENTS"
    assert wildcard_event.event_short == "2019*"
    assert wildcard_event.year == 2019
    assert wildcard_event.start_date == datetime(2019, 1, 1)
    assert wildcard_event.end_date == datetime(2019, 1, 1)


def test_team_models() -> None:
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)
    team_models = mytba.team_models

    assert len(team_models) == 2
    assert all([model.model_type == ModelType.TEAM for model in team_models])


def test_teams() -> None:
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)
    teams = mytba.teams

    assert len(teams) == 2
    assert all([type(team) is Team for team in teams])
    assert {team.key.id() for team in teams} == {"frc1", "frc2"}


def test_match_models() -> None:
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)
    match_models = mytba.match_models

    assert len(match_models) == 2
    assert all([model.model_type == ModelType.MATCH for model in match_models])


def test_matches() -> None:
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)
    matches = mytba.matches

    assert len(matches) == 2
    assert all([type(match) is Match for match in matches])
    assert {match.key.id() for match in matches} == {"2020miket_qm1", "2020miket_qm2"}


def test_event_matches() -> None:
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)
    event_matches = mytba.event_matches

    expected_key = ndb.Key(Event, "2020miket")

    keys = event_matches.keys()
    assert list(keys) == [expected_key]

    values = event_matches[expected_key]
    assert len(values) == 2
    assert all([type(value) is Match for value in values])


def test_favorite():
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)

    favorite = mytba.favorite(ModelType.TEAM, "frc2")
    assert favorite is None

    favorite = mytba.favorite(ModelType.TEAM, "frc1")
    assert favorite is not None


def test_subscription():
    models = _create_one_of_each_mytba_model()
    mytba = MyTBA(models)

    subscription = mytba.subscription(ModelType.TEAM, "frc1")
    assert subscription is None

    subscription = mytba.subscription(ModelType.TEAM, "frc2")
    assert subscription is not None
