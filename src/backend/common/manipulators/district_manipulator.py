from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.district import District
from backend.common.queries.district_query import DistrictHistoryQuery


class DistrictManipulator(ManipulatorBase[District]):
    """
    Handles District database writes
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.district_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: District,
        old_model: District,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> District:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model


@DistrictManipulator.register_post_update_hook
def district_post_update_hook(updated_models: List[TUpdatedModel[District]]) -> None:
    """
    To run after a district has been updated.
    For new districts, tries to guess the names based on other year's data
    """
    for updated in updated_models:
        if updated.is_new and (not updated.model.display_name):
            last_year_key = District.render_key_name(
                updated.model.year - 1, updated.model.abbreviation
            )
            last_year_district = District.get_by_id(last_year_key)
            update = False
            if last_year_district:
                if not updated.model.display_name:
                    updated.model.display_name = last_year_district.display_name
                    update = True
                if update:
                    DistrictManipulator.createOrUpdate(
                        updated.model, run_post_update_hook=False
                    )

        if "display_name" in updated.updated_attrs:
            # Set all other instances of this district to have the values
            all_past_years = DistrictHistoryQuery(updated.model.abbreviation).fetch()
            to_put = []
            for other_district in all_past_years:
                if other_district.year != updated.model.year:
                    other_district.display_name = updated.model.display_name
                    to_put.append(other_district)
            DistrictManipulator.createOrUpdate(to_put, run_post_update_hook=False)
