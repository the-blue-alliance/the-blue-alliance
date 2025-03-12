from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.regional_champs_pool import RegionalChampsPool


class RegionalChampsPoolManipulator(ManipulatorBase[RegionalChampsPool]):

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.regional_champs_pool_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: RegionalChampsPool,
        old_model: RegionalChampsPool,
        auto_union: bool = True,
    ) -> RegionalChampsPool:
        cls._update_attrs(new_model, old_model, auto_union)
        return old_model
