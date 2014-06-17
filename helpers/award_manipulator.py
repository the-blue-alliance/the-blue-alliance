import json

from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class AwardManipulator(ManipulatorBase):
    """
    Handle Award database writes.
    """
    @classmethod
    def clearCache(cls, affected_refs):
        CacheClearer.clear_award_and_references(affected_refs)

    @classmethod
    def updateMerge(self, new_award, old_award, auto_union=True):
        """
        Given an "old" and a "new" Award object, replace the fields in the
        "old" award that are present in the "new" award, but keep fields from
        the "old" award that are null in the "new" award.
        """
        immutable_attrs = [
            'event',
            'award_type_enum',
            'year',
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            'name_str',
        ]

        list_attrs = []

        auto_union_attrs = [
            'team_list',
            'recipient_json_list',
        ]

        json_attrs = {
            'recipient_json_list'
        }

        # if not auto_union, treat auto_union_attrs as list_attrs
        if not auto_union:
            list_attrs += auto_union_attrs
            auto_union_attrs = []

        for attr in attrs:
            if getattr(new_award, attr) is not None:
                if getattr(new_award, attr) != getattr(old_award, attr):
                    setattr(old_award, attr, getattr(new_award, attr))
                    old_award.dirty = True
            if getattr(new_award, attr) == "None":
                if getattr(old_award, attr, None) is not None:
                    setattr(old_award, attr, None)
                    old_award.dirty = True

        for attr in list_attrs:
            if len(getattr(new_award, attr)) > 0 or not auto_union:
                if getattr(new_award, attr) != getattr(old_award, attr):
                    setattr(old_award, attr, getattr(new_award, attr))
                    old_award.dirty = True

        for attr in auto_union_attrs:
            # JSON equaltiy comparison is not deterministic
            if attr in json_attrs:
                old_list = [json.loads(j) for j in getattr(old_award, attr)]
                new_list = [json.loads(j) for j in getattr(new_award, attr)]
            else:
                old_list = getattr(old_award, attr)
                new_list = getattr(new_award, attr)

            for item in new_list:
                if item not in old_list:
                    old_list.append(item)
                    old_award.dirty = True

            # Turn dicts back to JSON
            if attr in json_attrs:
                merged_list = [json.dumps(d) for d in old_list]
            else:
                merged_list = old_list

            setattr(old_award, attr, merged_list)

        return old_award
