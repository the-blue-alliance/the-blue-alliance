from datetime import datetime

import fakeredis
import pytest
from freezegun import freeze_time
from google.cloud import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.match import Match


@pytest.fixture()
def global_cache(ndb_client: ndb.Client):
    redis_client = fakeredis.FakeRedis()
    global_cache = ndb.RedisCache(redis_client)
    with ndb_client.context(global_cache=global_cache):
        yield redis_client


def do_test(model_class, global_cache, expected_ttl, **kwargs) -> None:
    model = model_class(**kwargs)
    model.put()

    context = ndb.get_context()
    assert context.global_cache is not None

    # The first datastore put will not write to the global cache
    cache_keys = global_cache.keys("*")
    assert len(cache_keys) == 0

    # The event will get written to the cache as a side effect of the read
    # Clear the context cache in between so we do not read previously written values
    context.clear_cache()
    model2 = model_class.get_by_id(model.key.id())
    assert model2 is not None

    # And now we expect a key to be present
    cache_keys = global_cache.keys("*")
    assert len(cache_keys) == 1

    # And for there to be an expiration that matches what we expect
    ttl = global_cache.ttl(cache_keys[0])
    assert ttl == expected_ttl


@pytest.mark.no_auto_ndb_context  # pyre-ignore[56]
def test_not_live_event_ttl(global_cache) -> None:
    do_test(
        Event,
        global_cache,
        expected_ttl=60 * 60 * 24,  # one day in seconds
        id="2019test",
        year=2019,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2019, 3, 1),
        end_date=datetime(2019, 3, 2),
        event_short="test",
    )


@pytest.mark.no_auto_ndb_context  # pyre-ignore[56]
@freeze_time("2019-03-01")
def test_live_event_ttl(global_cache) -> None:
    do_test(
        Event,
        global_cache,
        expected_ttl=61,
        id="2019test",
        year=2019,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2019, 3, 1),
        end_date=datetime(2019, 3, 2),
        event_short="test",
    )


@pytest.mark.no_auto_ndb_context  # pyre-ignore[56]
def test_not_live_event_match_ttl(global_cache) -> None:
    Event(
        id="2019test",
        year=2019,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2019, 3, 1),
        end_date=datetime(2019, 3, 2),
        event_short="test",
    ).put()

    do_test(
        Match,
        global_cache,
        expected_ttl=60 * 60 * 24,  # one day in seconds
        id="2019test_qm1",
        event=ndb.Key(Event, "2019test"),
        year=2019,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json='',
    )


@pytest.mark.no_auto_ndb_context  # pyre-ignore[56]
@freeze_time("2019-03-01")
def test_live_event_match_ttl(global_cache) -> None:
    Event(
        id="2019test",
        year=2019,
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=datetime(2019, 3, 1),
        end_date=datetime(2019, 3, 2),
        event_short="test",
    ).put()

    do_test(
        Match,
        global_cache,
        expected_ttl=61,
        id="2019test_qm1",
        event=ndb.Key(Event, "2019test"),
        year=2019,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json='',
    )
