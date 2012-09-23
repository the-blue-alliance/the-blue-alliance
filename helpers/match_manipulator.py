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
        attrs = [
            "alliances_json",
            "comp_level",
            "event",
            "game",
            "match_number",
            "no_auto_update",
            "set_number",
            "team_key_names",
            "tba_videos",
            "time",
            "youtube_videos"
        ]

        for attr in attrs:
            if getattr(new_match, attr) is not None:
                setattr(old_match, attr, getattr(new_match, attr))
        
        return old_match
