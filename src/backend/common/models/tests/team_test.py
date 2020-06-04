import pytest
from backend.common.models.team import Team

from .util import CITY_STATE_COUNTRY_PARAMETERS


def test_valid_key_names() -> None:
    assert Team.validate_key_name("frc177") is True
    assert Team.validate_key_name("frc1") is True


def test_invalida_key_names() -> None:
    assert Team.validate_key_name("bcr077") is False
    assert Team.validate_key_name("frc 011") is False
    assert Team.validate_key_name("frc711\\") is False


def test_key_name() -> None:
    team = Team(id="frc254", team_number=254)
    assert team.key_name == "frc254"


@pytest.mark.parametrize(
    "city, state, country, postalcode, output",
    [
        (None, None, None, None, ""),
        ("New York", None, None, None, "New York"),
        ("New York", "NY", None, None, "New York, NY"),
        ("New York", "NY", "USA", None, "New York, NY, USA"),
        ("New York", "NY", "USA", "10023", "New York, NY 10023, USA"),
        (None, "NY", None, None, "NY"),
        (None, "NY", "USA", None, "NY, USA"),
        (None, None, "USA", None, "USA"),
        ("New York", None, "USA", None, "New York, USA"),
    ],
)
def test_location(
    city: str, state: str, country: str, postalcode: str, output: str
) -> None:
    team = Team(city=city, state_prov=state, country=country, postalcode=postalcode,)
    assert team.location == output


@pytest.mark.parametrize(*CITY_STATE_COUNTRY_PARAMETERS)
def test_city_state_country(city: str, state: str, country: str, output: str) -> None:
    team = Team(city=city, state_prov=state, country=country,)
    assert team.city_state_country == output


def test_details_url() -> None:
    team = Team(id="frc254", team_number=254,)
    assert team.details_url == "/team/254"
