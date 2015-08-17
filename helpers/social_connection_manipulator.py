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
        """
        This model is immutable, so we can't merge things
        """

        immutable_attrs = [
            'parent_model',
            'social_type_enum',
            'foreign_key',
        ]

        return old_connection
