from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.location import Location
from backend.common.queries.dict_converters.converter_base import ConverterBase


def test_constructLocation_v3() -> None:
    location = Location(
        name="Test",
        formatted_address="1234 Street St., San Jose, CA 95120, USA",
        lat_lng=ndb.GeoPt(30, 40),
        city="San Jose",
        state_prov="California",
        state_prov_short="CA",
        country="United States",
        country_short="US",
        place_details={},
    )
    event = Event(
        normalized_location=location,
    )
    converted = ConverterBase.constructLocation_v3(event)

    assert converted["location_name"] == location.name
    assert converted["city"] == location.city
    assert converted["state_prov"] == location.state_prov_short
    assert converted["country"] == location.country_short_if_usa
    assert converted["lat"] == location.lat_lng.lat
    assert converted["lng"] == location.lat_lng.lon
