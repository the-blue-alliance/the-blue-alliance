import logging

from database.district_query import DistrictHistoryQuery
from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase
from models.district import District


class DistrictManipulator(ManipulatorBase):
    """
    Handles District database writes
    """

    @classmethod
    def postUpdateHook(cls, districts, updated_attr_list, is_new_list):
        """
        To run after a district has been updated.
        For new districts, tries to guess the names based on other year's data
        """
        for (district, is_new, updated_attrs) in zip(districts, is_new_list, updated_attr_list):
            if is_new and (not district.display_name or not district.elasticsearch_name):
                last_year_key = District.renderKeyName(district.year - 1, district.abbreviation)
                last_year_district = District.get_by_id(last_year_key)
                update = False
                if last_year_district:
                    if not district.display_name:
                        district.display_name = last_year_district.display_name
                        update = True
                    if not district.elasticsearch_name:
                        district.elasticsearch_name = last_year_district.elasticsearch_name
                        update = True
                    if update:
                        cls.createOrUpdate(district, run_post_update_hook=False)

            if 'display_name' in updated_attrs or 'elasticsearch_name' in updated_attrs:
                # Set all other instances of this district to have the values
                all_past_years = DistrictHistoryQuery(district.abbreviation).fetch()
                to_put = []
                for other_district in all_past_years:
                    if other_district.year != district.year:
                        other_district.display_name = district.display_name
                        other_district.elasticsearch_name = district.elasticsearch_name
                        to_put.append(other_district)
                cls.createOrUpdate(to_put, run_post_update_hook=False)

    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_district_cache_keys_and_controllers(affected_refs)

    @classmethod
    def updateMerge(self, new_district, old_district, auto_union=True):
        """
        Update and return Districts
        """
        immutable_attrs = [
            "year",
            "abbreviation",
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "display_name",
            "elasticsearch_name",
            "rankings",
            "advancement",
        ]

        old_district._updated_attrs = []
        for attr in attrs:
            if getattr(new_district, attr) is not None:
                if getattr(new_district, attr) != getattr(old_district, attr):
                    setattr(old_district, attr, getattr(new_district, attr))
                    old_district._updated_attrs.append(attr)
                    old_district.dirty = True

        return old_district
