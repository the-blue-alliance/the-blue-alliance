import json
import logging

from google.appengine.api import taskqueue

from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase
from helpers.notification_helper import NotificationHelper
from helpers.tbans_helper import TBANSHelper


class AwardManipulator(ManipulatorBase):
    """
    Handle Award database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_award_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postUpdateHook(cls, awards, updated_attr_list, is_new_list):
        # Note, updated_attr_list will always be empty, for now
        # Still needs to be implemented in updateMerge
        # See helpers.EventManipulator
        events = []
        for (award, updated_attrs) in zip(awards, updated_attr_list):
            event = award.event
            if event not in events:
                events.append(event)

        for event in events:
            if event.get().within_a_day:
                try:
                    NotificationHelper.send_award_update(event.get())
                except Exception:
                    logging.error("Error sending award update for {}".format(event.id()))
                try:
                    TBANSHelper.awards(event.get())
                except Exception, exception:
                    logging.error("Error sending {} award updates: {}".format(event.id(), exception))
                    logging.error(traceback.format_exc())

        # Enqueue task to calculate district points
        for event in events:
            taskqueue.add(
                url='/tasks/math/do/district_points_calc/{}'.format(event.id()),
                method='GET')

    @classmethod
    def updateMerge(self, new_award, old_award, auto_union=True):
        """
        Given an "old" and a "new" Award object, replace the fields in the
        "old" award that are present in the "new" award, but keep fields from
        the "old" award that are null in the "new" award.
        """
        immutable_attrs = [
            'event',
            'award_type_enum',
            'year',
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            'name_str',
        ]

        list_attrs = []

        auto_union_attrs = [
            'team_list',
            'recipient_json_list',
        ]

        json_attrs = {
            'recipient_json_list'
        }

        # if not auto_union, treat auto_union_attrs as list_attrs
        if not auto_union:
            list_attrs += auto_union_attrs
            auto_union_attrs = []

        for attr in attrs:
            if getattr(new_award, attr) is not None:
                if getattr(new_award, attr) != getattr(old_award, attr):
                    setattr(old_award, attr, getattr(new_award, attr))
                    old_award.dirty = True
            if getattr(new_award, attr) == "None":
                if getattr(old_award, attr, None) is not None:
                    setattr(old_award, attr, None)
                    old_award.dirty = True

        for attr in list_attrs:
            if len(getattr(new_award, attr)) > 0 or not auto_union:
                if getattr(new_award, attr) != getattr(old_award, attr):
                    setattr(old_award, attr, getattr(new_award, attr))
                    old_award.dirty = True

        for attr in auto_union_attrs:
            # JSON equaltiy comparison is not deterministic
            if attr in json_attrs:
                old_list = [json.loads(j) for j in getattr(old_award, attr)]
                new_list = [json.loads(j) for j in getattr(new_award, attr)]
            else:
                old_list = getattr(old_award, attr)
                new_list = getattr(new_award, attr)

            for item in new_list:
                if item not in old_list:
                    old_list.append(item)
                    old_award.dirty = True

            # Turn dicts back to JSON
            if attr in json_attrs:
                merged_list = [json.dumps(d) for d in old_list]
            else:
                merged_list = old_list

            setattr(old_award, attr, merged_list)

        return old_award
