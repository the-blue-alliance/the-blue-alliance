import pytest
from pyre_extensions import none_throws

from backend.common.manipulators.regional_champs_pool_manipulator import (
    RegionalChampsPoolManipulator,
)
from backend.common.models.regional_champs_pool import RegionalChampsPool


@pytest.mark.usefixtures("ndb_context")
def test_updateMerge() -> None:
    old_pool = RegionalChampsPool(id="2025", year=2025, adjustments={"frc254": 1})
    new_pool = RegionalChampsPool(id="2025", year=2025, adjustments={"frc254": 5})

    merged = RegionalChampsPoolManipulator.updateMerge(new_pool, old_pool)

    assert merged is old_pool
    assert merged.adjustments == {"frc254": 5}
    assert merged._updated_attrs == {"adjustments"}


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
def test_createOrUpdate() -> None:
    RegionalChampsPoolManipulator.createOrUpdate(
        RegionalChampsPool(id="2025", year=2025, adjustments={"frc254": 1})
    )
    RegionalChampsPoolManipulator.createOrUpdate(
        RegionalChampsPool(id="2025", year=2025, adjustments={"frc254": 2})
    )

    stored = none_throws(RegionalChampsPool.get_by_id("2025"))
    assert stored.adjustments == {"frc254": 2}
