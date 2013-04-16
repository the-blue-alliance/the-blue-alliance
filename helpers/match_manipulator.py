import logging
from helpers.manipulator_base import ManipulatorBase

class MatchManipulator(ManipulatorBase):
    """
    Handle Match database writes.
    """
    
    @classmethod
    def updateMerge(self, new_match, old_match):
        """
        Given an "old" and a "new" Match object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        immutable_attrs = [
            "comp_level",
            "event",
            "set_number",
            "match_number",
        ] # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "alliances_json",
            "game",
            "no_auto_update",
            "time",
            "time_string",
        ]

        list_attrs = [
            "team_key_names",
            "tba_videos",
            "youtube_videos"
        ]

        for attr in attrs:
            if getattr(new_match, attr) is not None:
                if getattr(new_match, attr) != getattr(old_match, attr):
                    setattr(old_match, attr, getattr(new_match, attr))
                    if attr == 'alliances_json':
                        # Necessary since 'alliances' doesn't get changed
                        # when mutating 'alliances_json'
                        old_match.clearAlliances()
                    old_match.dirty = True

        for attr in list_attrs:
            if len(getattr(new_match, attr)) > 0:
                if getattr(new_match, attr) != getattr(old_match, attr):
                    setattr(old_match, attr, getattr(new_match, attr))
                    old_match.dirty = True

        return old_match
