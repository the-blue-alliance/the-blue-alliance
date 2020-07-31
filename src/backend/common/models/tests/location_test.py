import pytest

from backend.common.models.location import Location
from backend.common.models.tests.util import CITY_STATE_COUNTRY_PARAMETERS


@pytest.mark.parametrize(
    "country, output",
    [("US", "USA"), ("USA", "USA"), ("United States", "USA"), ("Canada", "Canada")],
)
def test_country_short_if_usa(country: str, output: str) -> None:
    loc = Location(country=country)
    assert loc.country_short_if_usa == output


@pytest.mark.parametrize(
    CITY_STATE_COUNTRY_PARAMETERS[0], CITY_STATE_COUNTRY_PARAMETERS[1]
)
def test_city_state_country(city: str, state: str, country: str, output: str) -> None:
    loc = Location(city=city, state_prov_short=state, country=country,)
    assert loc.city_state_country == output
