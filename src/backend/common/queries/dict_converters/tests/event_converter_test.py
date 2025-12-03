import datetime

from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.location import Location
from backend.common.queries.dict_converters.event_converter import EventConverter


def test_eventConverter_v3_pre_2026_with_normalized_location(ndb_context) -> None:
    """
    Test that for events before 2026 with normalized_location,
    we use the normalized location data (with lat/lng and gmaps_place_id).
    """
    location = Location(
        name="Test Venue",
        formatted_address="123 Main St, San Jose, CA 95120, USA",
        lat_lng=ndb.GeoPt(37.335480, -121.893028),
        city="San Jose",
        state_prov="California",
        state_prov_short="CA",
        country="United States",
        country_short="US",
        postal_code="95120",
        place_id="ChIJ9T_5iuTKj4ARe3GfygqMnbk",
        place_details={"url": "https://maps.google.com/?cid=12345"},
    )
    event = Event(
        id="2025test",
        year=2025,
        name="Test Event 2025",
        short_name="Test",
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2025, 3, 15),
        end_date=datetime.datetime(2025, 3, 17),
        venue="FRC API Venue Name",
        venue_address="456 Another St",
        city="San Jose",
        state_prov="CA",
        country="USA",
        postalcode="95120",
        normalized_location=location,
        timezone_id="America/Los_Angeles",
        official=True,
    )

    converted = EventConverter.eventConverter_v3(event)

    assert converted["location_name"] == "Test Venue"
    assert converted["address"] == "123 Main St, San Jose, CA 95120, USA"
    assert converted["city"] == "San Jose"
    assert converted["state_prov"] == "CA"
    assert converted["country"] == "USA"
    assert converted["postal_code"] == "95120"
    assert converted["lat"] == 37.335480
    assert converted["lng"] == -121.893028
    assert converted["gmaps_place_id"] == "ChIJ9T_5iuTKj4ARe3GfygqMnbk"
    assert converted["gmaps_url"] == "https://maps.google.com/?cid=12345"


def test_eventConverter_v3_pre_2026_without_normalized_location(ndb_context) -> None:
    """
    Test that for events before 2026 without normalized_location,
    we fall back to basic venue/city/state_prov/country data.
    """
    event = Event(
        id="2025old",
        year=2025,
        name="Old Event 2025",
        short_name="Old",
        event_short="old",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2025, 3, 15),
        end_date=datetime.datetime(2025, 3, 17),
        venue="Old Venue",
        venue_address="789 Old St",
        city="Old City",
        state_prov="CA",
        country="USA",
        postalcode="95100",
        normalized_location=None,
        timezone_id="America/Los_Angeles",
        official=True,
    )

    converted = EventConverter.eventConverter_v3(event)

    assert converted["location_name"] == "Old Venue"
    assert converted["address"] == "789 Old St"
    assert converted["city"] == "Old City"
    assert converted["state_prov"] == "CA"
    assert converted["country"] == "USA"
    assert converted["postal_code"] == "95100"
    assert converted["lat"] is None
    assert converted["lng"] is None
    assert converted["gmaps_place_id"] is None
    assert converted["gmaps_url"] is None


def test_eventConverter_v3_2026_with_normalized_location(ndb_context) -> None:
    """
    Test that for events in 2026 and beyond, we use venue/venue_address
    from FRC API and lat/lng/gmaps_place_id is None even if normalized_location exists.
    """
    location = Location(
        name="Old Normalized Venue",
        formatted_address="123 Old St, San Jose, CA 95120, USA",
        lat_lng=ndb.GeoPt(37.335480, -121.893028),
        city="San Jose",
        state_prov="California",
        state_prov_short="CA",
        country="United States",
        country_short="US",
        postal_code="95120",
        place_id="ChIJ9T_5iuTKj4ARe3GfygqMnbk",
        place_details={"url": "https://maps.google.com/?cid=12345"},
    )
    event = Event(
        id="2026test",
        year=2026,
        name="Test Event 2026",
        short_name="Test",
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2026, 3, 15),
        end_date=datetime.datetime(2026, 3, 17),
        venue="FRC API Venue 2026",
        venue_address="100 New St",
        city="San Jose",
        state_prov="CA",
        country="USA",
        postalcode="95126",
        normalized_location=location,
        timezone_id="America/Los_Angeles",
        official=True,
    )

    converted = EventConverter.eventConverter_v3(event)

    assert converted["location_name"] == "FRC API Venue 2026"
    assert converted["address"] == "100 New St"
    assert converted["city"] == "San Jose"
    assert converted["state_prov"] == "CA"
    assert converted["country"] == "USA"
    assert converted["postal_code"] == "95126"
    assert converted["lat"] is None
    assert converted["lng"] is None
    assert converted["gmaps_place_id"] is None
    assert converted["gmaps_url"] is None


def test_eventConverter_v3_2026_without_venue_data(ndb_context) -> None:
    """
    Test that for events in 2026 and beyond without venue/venue_address,
    we fall back to basic location data from constructLocation_v3.
    """
    event = Event(
        id="2026minimal",
        year=2026,
        name="Minimal Event 2026",
        short_name="Minimal",
        event_short="minimal",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2026, 3, 15),
        end_date=datetime.datetime(2026, 3, 17),
        venue=None,
        venue_address=None,
        city="Minimal City",
        state_prov="CA",
        country="USA",
        postalcode="95000",
        normalized_location=None,
        timezone_id="America/Los_Angeles",
        official=True,
    )

    converted = EventConverter.eventConverter_v3(event)

    assert converted["location_name"] is None
    assert converted["address"] is None
    assert converted["city"] == "Minimal City"
    assert converted["state_prov"] == "CA"
    assert converted["country"] == "USA"
    assert converted["postal_code"] == "95000"
    assert converted["lat"] is None
    assert converted["lng"] is None
    assert converted["gmaps_place_id"] is None
    assert converted["gmaps_url"] is None
