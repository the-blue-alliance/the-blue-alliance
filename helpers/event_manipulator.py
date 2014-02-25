from helpers.manipulator_base import ManipulatorBase


class EventManipulator(ManipulatorBase):
    """
    Handle Event database writes.
    """

    @classmethod
    def updateMerge(self, new_event, old_event, auto_union=True):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        attrs = [
            "end_date",
            "event_short",
            "event_type_enum",
            "facebook_eid",
            "first_eid",
            "location",
            "timezone_id",
            "name",
            "official",
            "matchstats_json",
            "rankings_json",
            "short_name",
            "start_date",
            "venue",
            "venue_address",
            "webcast_json",
            "website",
            "year"
        ]

        list_attrs = []

        for attr in attrs:
            # Special case for rankings. Don't merge bad data.
            if attr == 'rankings_json':
                if new_event.rankings and len(new_event.rankings) <= 1:
                    continue
            if getattr(new_event, attr) is not None:
                if getattr(new_event, attr) != getattr(old_event, attr):
                    setattr(old_event, attr, getattr(new_event, attr))
                    old_event.dirty = True
            if getattr(new_event, attr) == "None":
                if getattr(old_event, attr, None) != None:
                    setattr(old_event, attr, None)
                    old_event.dirty = True

        for attr in list_attrs:
            if len(getattr(new_event, attr)) > 0:
                if getattr(new_event, attr) != getattr(old_event, attr):
                    setattr(old_event, attr, getattr(new_event, attr))
                    old_event.dirty = True

        return old_event
