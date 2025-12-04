from typing import TypedDict

from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event import Event
from backend.common.models.location import Location
from backend.common.queries.dict_converters.converter_base import ConverterBase


class DummyModel(ndb.Model):
    int_prop = ndb.IntegerProperty()


class DummyDict(TypedDict):
    int_val: int


class DummyConverter(ConverterBase):
    SUBVERSIONS = {
        ApiMajorVersion.API_V3: 0,
    }

    @classmethod
    def _convert_list(
        cls, model_list: list[DummyModel], version: ApiMajorVersion
    ) -> list[DummyDict]:
        return list(map(cls.converter_v3, model_list))

    @classmethod
    def converter_v3(cls, model: DummyModel) -> DummyDict:
        return {
            "int_val": model.int_prop,
        }


def test_convert_single() -> None:
    converted = DummyConverter(DummyModel(int_prop=604)).convert(ApiMajorVersion.API_V3)
    assert converted == {"int_val": 604}


def test_convert_multi() -> None:
    converted = DummyConverter(
        [DummyModel(int_prop=254), DummyModel(int_prop=604)]
    ).convert(ApiMajorVersion.API_V3)
    assert converted == [{"int_val": 254}, {"int_val": 604}]


def test_convert_none() -> None:
    converted = DummyConverter(None).convert(ApiMajorVersion.API_V3)
    assert converted is None


def test_constructLocation_v3_location_event() -> None:
    location = Location(
        name="Test",
        formatted_address="1234 Street St., San Jose, CA 95120, USA",
        lat_lng=ndb.GeoPt(30, 40),
        city="San Jose",
        state_prov="California",
        state_prov_short="CA",
        country="United States",
        country_short="US",
        place_details={"url": "some_url"},
    )
    event = Event(
        city="Anytown",
        state_prov="MI",
        country="USA",
        postalcode="90216",
        normalized_location=location,
    )
    converted = ConverterBase.constructLocation_v3(event)

    # Should use the Event location as opposed to geocoded location
    assert converted["city"] == event.city
    assert converted["country"] == event.country
    assert converted["state_prov"] == event.state_prov
    assert converted["postal_code"] == event.postalcode
    assert converted["location_name"] == "Test"
    assert converted["address"] == "1234 Street St., San Jose, CA 95120, USA"
    assert converted["lat"] is None
    assert converted["lng"] is None
    assert converted["gmaps_place_id"] is None
    assert converted["gmaps_url"] is None


def test_constructLocation_v3_location() -> None:
    location = Location(
        name="Test",
        formatted_address="1234 Street St., San Jose, CA 95120, USA",
        lat_lng=ndb.GeoPt(30, 40),
        city="San Jose",
        state_prov="California",
        state_prov_short="CA",
        country="United States",
        country_short="US",
        place_details={"url": "some_url"},
    )
    event = Event(normalized_location=location)
    converted = ConverterBase.constructLocation_v3(event)

    # Fallback to geocoded location if the event does not have location information
    assert converted["city"] == location.city
    assert converted["state_prov"] == location.state_prov_short
    assert converted["country"] == location.country_short_if_usa
    assert converted["postal_code"] == location.postal_code
    assert converted["location_name"] == "Test"
    assert converted["address"] == "1234 Street St., San Jose, CA 95120, USA"
    assert converted["lat"] is None
    assert converted["lng"] is None
    assert converted["gmaps_place_id"] is None
    assert converted["gmaps_url"] is None
