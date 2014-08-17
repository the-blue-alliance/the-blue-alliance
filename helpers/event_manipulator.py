from helpers.cache_clearer import CacheClearer
from helpers.event_helper import EventHelper
from helpers.manipulator_base import ManipulatorBase


class EventManipulator(ManipulatorBase):
    """
    Handle Event database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_event_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postUpdateHook(cls, event):
        """
        To run after a model has been updated
        """
        event.timezone_id = EventHelper.get_timezone_id(event.location, event.key.id())
        cls.createOrUpdate(event, run_post_update_hook=False)

    @classmethod
    def updateMerge(self, new_event, old_event, auto_union=True):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        attrs = [
            "alliance_selections_json",
            "district_points_json",
            "end_date",
            "event_short",
            "event_type_enum",
            "event_district_enum",
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
                if getattr(old_event, attr, None) is not None:
                    setattr(old_event, attr, None)
                    old_event.dirty = True

        for attr in list_attrs:
            if len(getattr(new_event, attr)) > 0:
                if getattr(new_event, attr) != getattr(old_event, attr):
                    setattr(old_event, attr, getattr(new_event, attr))
                    old_event.dirty = True

        return old_event
