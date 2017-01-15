from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class DistrictManipulator(ManipulatorBase):
    """
    Handles District database writes
    """

    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_district_cache_keys_and_controllers(affected_refs)

    @classmethod
    def updateMerge(self, new_district, old_district, auto_union=True):
        """
        Update and return Robots
        """
        immutable_attrs = [
            "year",
            "abbreviation",
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "display_name",
            "elasticsearch_name",
        ]

        for attr in attrs:
            if getattr(new_district, attr) is not None:
                if getattr(new_district, attr) != getattr(old_district, attr):
                    setattr(old_district, attr, getattr(new_district, attr))
                    old_district.dirty = True

        return old_district
