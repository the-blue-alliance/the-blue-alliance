from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.district import District


class DistrictManipulator(ManipulatorBase):
    """
    Handles District database writes
    """

    """
    @classmethod
    def postUpdateHook(cls, districts, updated_attr_list, is_new_list):
        '''
        To run after a district has been updated.
        For new districts, tries to guess the names based on other year's data
        '''
        for (district, is_new, updated_attrs) in zip(districts, is_new_list, updated_attr_list):
            if is_new and (not district.display_name):
                last_year_key = District.renderKeyName(district.year - 1, district.abbreviation)
                last_year_district = District.get_by_id(last_year_key)
                update = False
                if last_year_district:
                    if not district.display_name:
                        district.display_name = last_year_district.display_name
                        update = True
                    if update:
                        cls.createOrUpdate(district, run_post_update_hook=False)

            if 'display_name' in updated_attrs:
                # Set all other instances of this district to have the values
                all_past_years = DistrictHistoryQuery(district.abbreviation).fetch()
                to_put = []
                for other_district in all_past_years:
                    if other_district.year != district.year:
                        other_district.display_name = district.display_name
                        to_put.append(other_district)
                cls.createOrUpdate(to_put, run_post_update_hook=False)
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.district_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls, new_district: District, old_district: District, auto_union: bool = True
    ) -> District:
        cls._update_attrs(new_district, old_district, auto_union)
        return old_district
