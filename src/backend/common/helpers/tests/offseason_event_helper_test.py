import datetime

import pytest

from backend.common.consts.event_type import EventType
from backend.common.helpers.offseason_event_helper import OffseasonEventHelper
from backend.common.models.event import Event


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub):
    yield


def test_is_direct_match_key_name():
    first_event_match = Event(year=2020, event_short="zor")
    second_event_match = Event(year=2020, event_short="zor")
    third_event_match = Event(year=2020, event_short="iri")

    assert OffseasonEventHelper.is_direct_match(first_event_match, second_event_match)
    assert not OffseasonEventHelper.is_direct_match(
        first_event_match, third_event_match
    )


def test_is_direct_match_key_name_with_first_code():
    tba_event_one = Event(year=2020, first_code="zor", event_short="zorr")
    tba_event_two = Event(year=2020, first_code="iri", event_short="irii")
    first_event = Event(year=2020, event_short="zor")

    assert OffseasonEventHelper.is_direct_match(tba_event_one, first_event)
    assert not OffseasonEventHelper.is_direct_match(tba_event_two, first_event)


def test_is_maybe_match():
    event_one = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    event_two = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    assert OffseasonEventHelper.is_maybe_match(event_one, event_two)


def test_is_maybe_match_wrong_start():
    event_one = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    event_two = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=13, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    assert not OffseasonEventHelper.is_maybe_match(event_one, event_two)
    event_two.start_date = event_one.start_date
    assert OffseasonEventHelper.is_maybe_match(event_one, event_two)


def test_is_maybe_match_wrong_end():
    event_one = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    event_two = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=16, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    assert not OffseasonEventHelper.is_maybe_match(event_one, event_two)
    event_two.end_date = event_one.end_date
    assert OffseasonEventHelper.is_maybe_match(event_one, event_two)


def test_is_maybe_match_wrong_city():
    event_one = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    event_two = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="Sandusky",
        state_prov="OH",
    )
    assert not OffseasonEventHelper.is_maybe_match(event_one, event_two)
    event_two.city = event_one.city
    assert OffseasonEventHelper.is_maybe_match(event_one, event_two)


def test_is_maybe_match_wrong_state_prov():
    event_one = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="OH",
    )
    event_two = Event(
        start_date=datetime.datetime(
            year=2020, month=7, day=14, hour=0, minute=0, second=0
        ),
        end_date=datetime.datetime(
            year=2020, month=7, day=15, hour=23, minute=59, second=59
        ),
        city="London",
        state_prov="CA",
    )
    assert not OffseasonEventHelper.is_maybe_match(event_one, event_two)
    event_two.state_prov = event_one.state_prov
    assert OffseasonEventHelper.is_maybe_match(event_one, event_two)


def test_categorize_offseasons():
    # Setup some existing TBA events in the database - these will be queried for our test
    preseason_event = Event(
        id="2016mipre",
        name="Michigan Preseason Event",
        event_type_enum=EventType.PRESEASON,
        short_name="MI Preseason",
        event_short="mipre",
        first_code="mierp",
        year=2016,
        end_date=datetime.datetime(2016, 2, 25),
        official=False,
        city="Anytown",
        state_prov="MI",
        country="USA",
        venue="Some Venue",
        venue_address="Some Venue, Anytown, MI, USA",
        timezone_id="America/New_York",
        start_date=datetime.datetime(2016, 2, 24),
        webcast_json="",
        website=None,
    )
    preseason_event.put()

    offseason_event = Event(
        id="2016mioff",
        name="Michigan Offseason Event",
        event_type_enum=EventType.OFFSEASON,
        short_name="MI Offseason",
        event_short="mioff",
        year=2016,
        end_date=datetime.datetime(2016, 6, 25),
        official=False,
        city="Anytown",
        state_prov="MI",
        country="USA",
        venue="Some Venue",
        venue_address="Some Venue, Anytown, MI, USA",
        timezone_id="America/New_York",
        start_date=datetime.datetime(2016, 6, 24),
        webcast_json="",
        website=None,
    )
    offseason_event.put()

    # Exact match
    first_preseason = Event(year=2016, event_short="mierp")
    # Indirect match
    first_offseason = Event(
        year=2016,
        event_short="miffo",
        start_date=datetime.datetime(2016, 6, 24),
        end_date=datetime.datetime(2016, 6, 25),
        city="Anytown",
        state_prov="MI",
    )
    first_new_event = Event(year=2016, event_short="minew")
    first_events = [first_preseason, first_offseason, first_new_event]

    existing, new = OffseasonEventHelper.categorize_offseasons(2016, first_events)
    # Should have two existing events
    assert len(existing) == 2
    assert (preseason_event, first_preseason) in existing
    assert (offseason_event, first_offseason) in existing

    # Should have one new event
    assert len(new) == 1
    assert new == [first_new_event]


def test_categorize_offseasons_no_events():
    first_preseason = Event(year=2016, event_short="mierp")
    first_offseason = Event(
        year=2016,
        event_short="miffo",
        start_date=datetime.datetime(2016, 6, 24),
        end_date=datetime.datetime(2016, 6, 25),
        city="Anytown",
        state_prov="MI",
    )
    first_new_event = Event(year=2016, event_short="minew")
    first_events = [first_preseason, first_offseason, first_new_event]

    existing, new = OffseasonEventHelper.categorize_offseasons(2016, first_events)
    # Should have no existing events
    assert len(existing) == 0
    assert len(new) == 3
