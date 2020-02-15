import logging
import traceback

from google.appengine.api import taskqueue

from helpers.cache_clearer import CacheClearer
from helpers.firebase.firebase_pusher import FirebasePusher
from helpers.manipulator_base import ManipulatorBase
from helpers.notification_helper import NotificationHelper
from helpers.tbans_helper import TBANSHelper

from models.event import Event
from helpers.manipulator_base import ManipulatorBase


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
            if event.within_a_day and "alliance_selections" in updated_attrs:
                try:
                    NotificationHelper.send_alliance_update(event)
                except Exception:
                    logging.error("Error sending alliance update notification for {}".format(event.key_name))
                    logging.error(traceback.format_exc())
                try:
                    TBANSHelper.alliance_selection(event)
                except Exception:
                    logging.error("Error sending alliance update notification for {}".format(event.key_name))
                    logging.error(traceback.format_exc())

            # Enqueue task to calculate district points
            try:
                taskqueue.add(
                    url='/tasks/math/do/district_points_calc/{}'.format(event.key.id()),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing district_points_calc for {}".format(event.key.id()))
                logging.error(traceback.format_exc())

            # Enqueue task to calculate event team status
            try:
                taskqueue.add(
                    url='/tasks/math/do/event_team_status/{}'.format(event.key.id()),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing event_team_status for {}".format(event.key.id()))
                logging.error(traceback.format_exc())

            try:
                FirebasePusher.update_event_details(event_details)
            except Exception:
                logging.warning("Firebase update_event_details failed!")

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
            'insights',
            'predictions',
            'rankings',
            'rankings2',
            'playoff_advancement'
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
