import logging
import traceback

from google.appengine.api import taskqueue

from helpers.cache_clearer import CacheClearer
from helpers.event_helper import EventHelper
from helpers.manipulator_base import ManipulatorBase
from helpers.notification_helper import NotificationHelper


class EventManipulator(ManipulatorBase):
    """
    Handle Event database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_event_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postUpdateHook(cls, events, updated_attr_list, is_new_list):
        """
        To run after models have been updated
        """
        for (event, updated_attrs) in zip(events, updated_attr_list):
            try:
                if event.within_a_day and "alliance_selections_json" in updated_attrs:
                    # Send updated alliances notification
                    logging.info("Sending alliance notifications for {}".format(event.key_name))
                    NotificationHelper.send_alliance_update(event)
            except Exception:
                logging.error("Error sending alliance update notification for {}".format(event.key_name))
                logging.error(traceback.format_exc())

            try:
                event.timezone_id = EventHelper.get_timezone_id(event.location, event.key.id())
                cls.createOrUpdate(event, run_post_update_hook=False)
            except Exception:
                logging.warning("Timezone update for event {} failed!".format(event.key_name))

        # Enqueue task to calculate district points
        for event in events:
            taskqueue.add(
                url='/tasks/math/do/district_points_calc/{}'.format(event.key.id()),
                method='GET')

    @classmethod
    def updateMerge(self, new_event, old_event, auto_union=True):
        """
        Given an "old" and a "new" Event object, replace the fields in the
        "old" event that are present in the "new" event, but keep fields from
        the "old" event that are null in the "new" event.
        """
        attrs = [
            "alliance_selections_json",
            "district_points_json",
            "end_date",
            "event_short",
            "event_type_enum",
            "event_district_enum",
            "custom_hashtag",
            "facebook_eid",
            "first_eid",
            "location",
            "city",
            "state_prov",
            "country",
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

        old_event._updated_attrs = []

        for attr in attrs:
            # Special case for rankings. Don't merge bad data.
            if attr == 'rankings_json':
                if new_event.rankings and len(new_event.rankings) <= 1:
                    continue
            if getattr(new_event, attr) is not None:
                if getattr(new_event, attr) != getattr(old_event, attr):
                    setattr(old_event, attr, getattr(new_event, attr))
                    old_event._updated_attrs.append(attr)
                    old_event.dirty = True
            if getattr(new_event, attr) == "None":
                if getattr(old_event, attr, None) is not None:
                    setattr(old_event, attr, None)
                    old_event._updated_attrs.append(attr)
                    old_event.dirty = True

        for attr in list_attrs:
            if len(getattr(new_event, attr)) > 0:
                if getattr(new_event, attr) != getattr(old_event, attr):
                    setattr(old_event, attr, getattr(new_event, attr))
                    old_event._updated_attrs.append(attr)
                    old_event.dirty = True

        return old_event
