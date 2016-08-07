from helpers.manipulator_base import ManipulatorBase


class EventDetailsManipulator(ManipulatorBase):
    """
    Handle EventDetails database writes.
    """
    @classmethod
    def updateMerge(self, new_event_details, old_event_details, auto_union=True):
        """
        Given an "old" and a "new" EventDetails object, replace the fields in the
        "old" event that are present in the "new" EventDetails, but keep fields from
        the "old" event that are null in the "new" EventDetails.
        """
        attrs = [
            'alliance_selections',
            'district_points',
            'matchstats',
            'rankings',
        ]

        for attr in attrs:
            # Special case for rankings (only first row). Don't merge bad data.
            if attr == 'rankings':
                if new_event_details.rankings and len(new_event_details.rankings) <= 1:
                    continue
            if getattr(new_event_details, attr) is not None:
                if getattr(new_event_details, attr) != getattr(old_event_details, attr):
                    setattr(old_event_detail, attr, getattr(new_event_detail, attr))
                    old.event_detail.dirty = True
        return old_event_detials
