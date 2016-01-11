from helpers.manipulator_base import ManipulatorBase


class SocialConnectionManipulator(ManipulatorBase):
    """
    Handle SocialConnection database writes
    """

    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        # TODO cache clearing
        return []

    @classmethod
    def updateMerge(self, new_connection, old_connection, auto_union=True):

        immutable_attrs = [
            'social_type_enum',
            'foreign_key',
        ]

        list_attrs = []

        auto_union_attrs = [
            'references',
        ]

        # if not auto_union, treat auto_union_attrs as list_attrs
        if not auto_union:
            list_attrs += auto_union_attrs
            auto_union_attrs = []

        for attr in list_attrs:
            if len(getattr(new_connection, attr)) > 0:
                if getattr(new_connection, attr) != getattr(old_connection, attr):
                    setattr(old_connection, attr, getattr(new_connection, attr))
                    old_connection.dirty = True

        for attr in auto_union_attrs:
            old_set = set(getattr(old_connection, attr))
            new_set = set(getattr(new_connection, attr))
            unioned = old_set.union(new_set)
            if unioned != old_set:
                setattr(old_connection, attr, list(unioned))
                old_connection.dirty = True

        return old_connection
