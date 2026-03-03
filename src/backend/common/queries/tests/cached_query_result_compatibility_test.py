import pickle

import pytest
from google.appengine.ext import ndb

from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.media import Media
from backend.common.models.team import Team

"""
These tests verify that NDB model objects round-trip correctly through pickle
serialization, both directly and via the CachedQueryResult property.
"""


@pytest.fixture(autouse=True)
def clean_up_global_state():
    ndb.get_context().clear_cache()
    yield
    ndb.get_context().clear_cache()


class ModelWithInt(ndb.Model):
    int_prop = ndb.IntegerProperty()


def test_round_trip_model_pickle_integer() -> None:
    ModelWithInt(
        id="test_model",
        int_prop=2018,
    ).put()
    model = ModelWithInt.get_by_id("test_model")

    pickled = pickle.dumps(model)
    check = pickle.loads(pickled)

    assert check == model


class ModelWithIntRepeated(ndb.Model):
    int_prop = ndb.IntegerProperty(repeated=True)


def test_round_trip_model_pickle_integer_repeated() -> None:
    ModelWithIntRepeated(
        id="test_model",
        int_prop=[2018, 2019, 2020],
    ).put()
    model = ModelWithIntRepeated.get_by_id("test_model")

    pickled = pickle.dumps(model)
    check = pickle.loads(pickled)

    assert check == model


class ModelWithString(ndb.Model):
    str_prop = ndb.StringProperty()


def test_round_trip_model_pickle_string() -> None:
    ModelWithString(
        id="test_model",
        str_prop="abc123",
    ).put()
    model = ModelWithString.get_by_id("test_model")

    pickled = pickle.dumps(model)
    check = pickle.loads(pickled)

    assert check == model


def test_round_trip_model_pickle_string_non_unicode() -> None:
    ModelWithString(
        id="test_model",
        str_prop="PrepaTec CEM&Instituto Tecnológico y de Estudios Superiores de Monterrey",
    ).put()
    model = ModelWithString.get_by_id("test_model")

    pickled = pickle.dumps(model)
    check = pickle.loads(pickled)

    assert check == model


class ModelWithKey(ndb.Model):
    key_prop = ndb.KeyProperty()


def test_round_trip_model_pickle_key() -> None:
    ModelWithKey(
        id="test_model",
        key_prop=ndb.Key(Media, "test_media"),
    ).put()
    model = ModelWithKey.get_by_id("test_model")

    pickled = pickle.dumps(model)
    check = pickle.loads(pickled)

    assert check == model


def test_round_trip_model_pickle_media() -> None:
    Media(
        id="test_media",
        details_json='{"base64Image": "iVBORw0KGgo="}',
        foreign_key="avatar_2018_frc999",
        media_type_enum=12,
        private_details_json=None,
        references=[
            ndb.Key("Team", "frc999", app="s~tbatv-prod-hrd"),
        ],
        year=2018,
    ).put()
    model = Media.get_by_id("test_media")

    pickled = pickle.dumps(model)
    check = pickle.loads(pickled)

    assert check == model


def test_round_trip_model_pickle_event_team() -> None:
    k = EventTeam(
        id="2020test_frc254",
        team=ndb.Key(Team, "frc254"),
        event=ndb.Key(Event, "2020test"),
        year=2020,
    ).put()
    model = k.get()

    pickled = pickle.dumps(model)
    check = pickle.loads(pickled)

    assert check == model


def test_round_trip_cached_query_result() -> None:
    """Verify that models survive the full CachedQueryResult property path."""
    team_list = [
        Team(id="frc254", team_number=254),
        Team(id="frc1678", team_number=1678),
    ]
    for t in team_list:
        t.put()
    team_list = [Team.get_by_id(str(t.key.id())) for t in team_list]

    cqr = CachedQueryResult(id="test_cache", result=team_list)
    cqr.put()

    loaded = CachedQueryResult.get_by_id("test_cache")
    assert loaded is not None
    assert loaded.result == team_list
