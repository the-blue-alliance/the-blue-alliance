import pytest

from backend.common.models.team import Team
from backend.common.models.tests.util import (
    CITY_STATE_COUNTRY_PARAMETERS,
    LOCATION_PARAMETERS,
)


@pytest.mark.parametrize("key", ["frc177", "frc1"])
def test_valid_key_names(key: str) -> None:
    assert Team.validate_key_name(key) is True


@pytest.mark.parametrize("key", ["bcr077", "frc 011", "frc711\\"])
def test_invalid_key_names(key: str) -> None:
    assert Team.validate_key_name(key) is False


def test_key_name() -> None:
    team = Team(id="frc254", team_number=254)
    assert team.key_name == "frc254"


@pytest.mark.parametrize(LOCATION_PARAMETERS[0], LOCATION_PARAMETERS[1])
def test_location(
    city: str, state: str, country: str, postalcode: str, output: str
) -> None:
    team = Team(city=city, state_prov=state, country=country, postalcode=postalcode,)
    assert team.location == output


@pytest.mark.parametrize(
    CITY_STATE_COUNTRY_PARAMETERS[0], CITY_STATE_COUNTRY_PARAMETERS[1]
)
def test_city_state_country(city: str, state: str, country: str, output: str) -> None:
    team = Team(city=city, state_prov=state, country=country,)
    assert team.city_state_country == output


def test_details_url() -> None:
    team = Team(id="frc254", team_number=254,)
    assert team.details_url == "/team/254"
