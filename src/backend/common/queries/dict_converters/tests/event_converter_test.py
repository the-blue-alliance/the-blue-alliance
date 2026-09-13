from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.location import Location
from backend.common.queries.dict_converters.district_converter import DistrictConverter
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
    district = District(
        id="2025ne",
        year=2025,
        abbreviation="ne",
        display_name="New England",
    )
    district.put()
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
        district_key=ndb.Key(District, "2025ne"),
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
    assert converted["district"] == DistrictConverter.districtConverter_v3(district)


def test_eventConverter_v3_omits_nexus_code_for_api(ndb_context) -> None:
    event = Event(
        id="2026demo",
        year=2026,
        event_short="demo",
        event_type_enum=EventType.REGIONAL,
        nexus_code="demo0755",
    )

    converted = EventConverter.eventConverter_v3(event)

    assert "nexus_code_for_api" not in converted


def test_eventsConverter_v3_batched_district_lookups(monkeypatch, ndb_context) -> None:
    district_ne = District(
        id="2025ne",
        year=2025,
        abbreviation="ne",
        display_name="New England",
    )
    district_fim = District(
        id="2025fim",
        year=2025,
        abbreviation="fim",
        display_name="FIRST in Michigan",
    )
    district_ne.put()
    district_fim.put()

    ne_key = ndb.Key(District, "2025ne")
    fim_key = ndb.Key(District, "2025fim")
    missing_key = ndb.Key(District, "2025nonexistent")

    e1 = Event(
        id="2025ne1", year=2025, event_type_enum=EventType.DISTRICT, district_key=ne_key
    )
    e2 = Event(
        id="2025ne2", year=2025, event_type_enum=EventType.DISTRICT, district_key=ne_key
    )
    e3 = Event(
        id="2025fim1",
        year=2025,
        event_type_enum=EventType.DISTRICT,
        district_key=fim_key,
    )
    e4 = Event(
        id="2025fim2",
        year=2025,
        event_type_enum=EventType.DISTRICT,
        district_key=fim_key,
    )
    e5 = Event(
        id="2025regional",
        year=2025,
        event_type_enum=EventType.REGIONAL,
        district_key=None,
    )
    e6 = Event(
        id="2025missing",
        year=2025,
        event_type_enum=EventType.DISTRICT,
        district_key=missing_key,
    )

    events = [e1, e2, e3, e4, e5, e6]

    from unittest.mock import MagicMock

    get_multi_mock = MagicMock(wraps=ndb.get_multi)
    monkeypatch.setattr(ndb, "get_multi", get_multi_mock)

    converted_events = EventConverter.eventsConverter_v3(events)

    # get_multi should have been called exactly once with the unique district keys
    assert get_multi_mock.call_count == 1
    call_args = get_multi_mock.call_args[0][0]
    assert set(call_args) == {ne_key, fim_key, missing_key}

    expected_ne_district = DistrictConverter.districtConverter_v3(district_ne)
    expected_fim_district = DistrictConverter.districtConverter_v3(district_fim)

    assert converted_events[0]["district"] == expected_ne_district
    assert converted_events[1]["district"] == expected_ne_district
    assert converted_events[2]["district"] == expected_fim_district
    assert converted_events[3]["district"] == expected_fim_district
    assert converted_events[4]["district"] is None
    assert converted_events[5]["district"] is None


def test_eventConverter_v3_with_district_map(monkeypatch, ndb_context) -> None:
    district = District(
        id="2025ne",
        year=2025,
        abbreviation="ne",
        display_name="New England",
    )
    expected_district_dict = DistrictConverter.districtConverter_v3(district)
    district_key = ndb.Key(District, "2025ne")

    event = Event(
        id="2025test",
        year=2025,
        event_type_enum=EventType.DISTRICT,
        district_key=district_key,
    )

    from unittest.mock import MagicMock

    get_async_mock = MagicMock(wraps=ndb.Key.get_async)
    monkeypatch.setattr(ndb.Key, "get_async", get_async_mock)

    # When district_map is passed, get_async should not be called
    converted = EventConverter.eventConverter_v3(
        event, district_map={district_key: expected_district_dict}
    )
    assert converted["district"] == expected_district_dict
    get_async_mock.assert_not_called()
