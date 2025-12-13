from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.regional_pool_team import RegionalPoolTeam


class RegionalPoolTeamManipulator(ManipulatorBase[RegionalPoolTeam]):
    """
    handle RegionalPoolTeam writes
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.regionalpoolteam_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: RegionalPoolTeam,
        old_model: RegionalPoolTeam,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ):
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
