from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.location import Location
from backend.common.queries.dict_converters.event_converter import EventConverter


def test_eventConverter_v3_with_event_location(ndb_context) -> None:
    """
    Test to ensure that in the case the Event has a `venue` and `venue_address`
    we use that for `location_name` and `address`, as opposed to geocoded location
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
        event_type_enum=EventType.REGIONAL,
        venue="FRC API Venue Name",
        venue_address="456 Another St",
        city="San Jose",
        state_prov="CA",
        country="USA",
        postalcode="95120",
        normalized_location=location,
    )

    converted = EventConverter.eventConverter_v3(event)

    assert converted["location_name"] == "FRC API Venue Name"
    assert converted["address"] == "456 Another St"
    assert converted["city"] == "San Jose"
    assert converted["state_prov"] == "CA"
    assert converted["country"] == "USA"
    assert converted["postal_code"] == "95120"
    assert converted["lat"] is None
    assert converted["lng"] is None
    assert converted["gmaps_place_id"] is None
    assert converted["gmaps_url"] is None


def test_eventConverter_v3_without_event_location(ndb_context) -> None:
    """
    Test that in the event the event does not have location data, we use the normalized
    location to populate the `location_name` and `address`
    """
    """
    Test to ensure that in the case the Event has a `venue` and `venue_address`
    we use that for `location_name` and `address`, as opposed to geocoded location
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
        event_type_enum=EventType.REGIONAL,
        venue=None,
        venue_address=None,
        city="San Jose",
        state_prov="CA",
        country="USA",
        postalcode="95120",
        normalized_location=location,
    )

    converted = EventConverter.eventConverter_v3(event)

    assert converted["location_name"] == "Test Venue"
    assert converted["address"] == "123 Main St, San Jose, CA 95120, USA"
    assert converted["city"] == "San Jose"
    assert converted["state_prov"] == "CA"
    assert converted["country"] == "USA"
    assert converted["postal_code"] == "95120"
    assert converted["lat"] is None
    assert converted["lng"] is None
    assert converted["gmaps_place_id"] is None
    assert converted["gmaps_url"] is None
