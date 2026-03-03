import datetime
from unittest.mock import patch

from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.models.team import Team
from backend.web.renderers.team_renderer import TeamRenderer


# Nullapalooza: test that corrupted Event entities are filtered out
def test_fetch_events_skips_null_year_event(ndb_stub) -> None:
    """Events with year=None should be skipped instead of crashing."""
    team = Team(id="frc254", team_number=254)
    team.put()

    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=0,
        start_date=datetime.datetime(2020, 3, 1),
        end_date=datetime.datetime(2020, 3, 3),
    ).put()

    # Simulate a corrupted event with year=None by patching the query result
    corrupted_event = Event(
        id="2020bad",
        year=2020,
        event_short="bad",
        event_type_enum=0,
    )
    corrupted_event.year = None  # type: ignore[assignment]

    valid_event = Event.get_by_id("2020casj")
    assert valid_event is not None

    with patch(
        "backend.web.renderers.team_renderer.event_query.TeamYearEventsQuery"
    ) as mock_query_cls:
        future = ndb.Future()
        future.set_result([corrupted_event, valid_event])
        mock_query_cls.return_value.fetch_async.return_value = future

        result = TeamRenderer._fetch_events_async(team, Year(2020)).get_result()

    assert len(result) == 1
    assert result[0].key.id() == "2020casj"


# Nullapalooza: test that None events from ndb.get_multi_async are filtered out
def test_fetch_events_skips_none_events(ndb_stub) -> None:
    """None results from get_multi_async should be skipped."""
    team = Team(id="frc254", team_number=254)
    team.put()

    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=0,
        start_date=datetime.datetime(2020, 3, 1),
        end_date=datetime.datetime(2020, 3, 3),
    ).put()

    valid_event = Event.get_by_id("2020casj")
    assert valid_event is not None

    with patch(
        "backend.web.renderers.team_renderer.event_query.TeamYearEventsQuery"
    ) as mock_query_cls:
        future = ndb.Future()
        future.set_result([None, valid_event])
        mock_query_cls.return_value.fetch_async.return_value = future

        result = TeamRenderer._fetch_events_async(team, Year(2020)).get_result()

    assert len(result) == 1
    assert result[0].key.id() == "2020casj"
