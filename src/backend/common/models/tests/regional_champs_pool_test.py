from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.regional_champs_pool_manipulator import (
    RegionalChampsPoolManipulator,
)
from backend.common.models.regional_champs_pool import RegionalChampsPool


def test_key_name() -> None:
    pool = RegionalChampsPool(id="2025", year=2025)
    assert pool.key_name == "2025"
    assert RegionalChampsPool.render_key_name(2025) == "2025"
    assert pool._affected_references == {"year": set()}


def test_validate_key_name() -> None:
    assert SeasonHelper.MIN_REGIONAL_CMP_POOL_YEAR == 2025
    assert RegionalChampsPool.validate_key_name("2025") is True
    # Before the regional pool existed
    assert RegionalChampsPool.validate_key_name("2024") is False
    assert RegionalChampsPool.validate_key_name("2025ct") is False
    assert RegionalChampsPool.validate_key_name("") is False


def test_get_for_year_invalid_year() -> None:
    assert RegionalChampsPool.get_for_year(2024) is None


def test_get_for_year() -> None:
    assert RegionalChampsPool.get_for_year(2025) is None

    RegionalChampsPoolManipulator.createOrUpdate(
        RegionalChampsPool(
            id="2025",
            year=2025,
            rankings=[],
            advancement={},
            adjustments={},
        )
    )

    pool = RegionalChampsPool.get_for_year(2025)
    assert pool is not None
    assert pool.key_name == "2025"
    assert pool.year == 2025
