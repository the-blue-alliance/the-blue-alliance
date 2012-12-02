from helpers.manipulator_base import ManipulatorBase

class EventTeamManipulator(ManipulatorBase):
    """
    Handle EventTeam database writes.
    """

    @classmethod
    def updateMerge(self, new_event_team, old_event_team):
        """
        It is impossible to mutate an EventTeam. Just return the existing one.
        """

        immutable_attrs = [
            "event",
            "team",
            "year",
        ] # These build key_name, and cannot be changed without deleting the model.

        return old_event_team
