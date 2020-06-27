import pytest

from backend.common.models.district import District


@pytest.mark.parametrize("key", ["2019ne", "2010fim"])
def test_valid_key_names(key: str) -> None:
    assert District.validate_key_name(key) is True


@pytest.mark.parametrize("key", ["2020", "asdf", "frc177"])
def test_invalid_key_names(key: str) -> None:
    assert District.validate_key_name(key) is False


def test_render_key_name() -> None:
    assert District.renderKeyName(2016, "ne") == "2016ne"


def test_key_name() -> None:
    d = District(id="2020ne", year=2020, abbreviation="ne",)
    assert d.key_name == "2020ne"


def test_render_name() -> None:
    d = District(id="2020ne", display_name="New England",)
    assert d.render_name == "New England"


def test_render_name_falls_back_to_code() -> None:
    d = District(id="2020ne", abbreviation="ne",)
    assert d.render_name == "NE"
