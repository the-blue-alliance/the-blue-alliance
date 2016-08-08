import logging
import traceback

from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase
from helpers.notification_helper import NotificationHelper

from models.event import Event


class EventDetailsManipulator(ManipulatorBase):
    """
    Handle EventDetails database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_event_details_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postUpdateHook(cls, event_details_list, updated_attr_list, is_new_list):
        """
        To run after models have been updated
        """
        for (event_details, updated_attrs) in zip(event_details_list, updated_attr_list):
            event = Event.get_by_id(event_details.key.id())
            try:
                if event.within_a_day and "alliance_selections" in updated_attrs:
                    # Send updated alliances notification
                    logging.info("Sending alliance notifications for {}".format(event.key_name))
                    NotificationHelper.send_alliance_update(event)
            except Exception:
                logging.error("Error sending alliance update notification for {}".format(event.key_name))
                logging.error(traceback.format_exc())

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

        old_event_details._updated_attrs = []

        for attr in attrs:
            # Special case for rankings (only first row). Don't merge bad data.
            if attr == 'rankings':
                if new_event_details.rankings and len(new_event_details.rankings) <= 1:
                    continue
            if getattr(new_event_details, attr) is not None:
                if getattr(new_event_details, attr) != getattr(old_event_details, attr):
                    setattr(old_event_details, attr, getattr(new_event_details, attr))
                    old_event_details._updated_attrs.append(attr)
                    old_event_details.dirty = True
        return old_event_details
