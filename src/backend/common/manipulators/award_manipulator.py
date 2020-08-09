import json

from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.award import Award


class AwardManipulator(ManipulatorBase[Award]):
    """
    Handle Award database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_award_cache_keys_and_controllers(affected_refs)
    """

    """
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
    """

    @classmethod
    def updateMerge(
        cls, new_award: Award, old_award: Award, auto_union: bool = True
    ) -> Award:
        auto_union_list_attrs = {
            "team_list",
            "recipient_json_list",
        }

        json_list_attrs = {"recipient_json_list"}

        cls._update_attrs(new_award, old_award, auto_union)

        for attr in auto_union_list_attrs:
            # JSON equaltiy comparison is not deterministic
            if attr in json_list_attrs:
                old_list = [json.loads(j) for j in getattr(old_award, attr)]
                new_list = [json.loads(j) for j in getattr(new_award, attr)]
            else:
                old_list = getattr(old_award, attr)
                new_list = getattr(new_award, attr)

            if auto_union:
                for item in new_list:
                    if item not in old_list:
                        old_list.append(item)
                        old_award._dirty = True
            else:
                old_list = new_list

            # Turn dicts back to JSON
            if attr in json_list_attrs:
                merged_list = [json.dumps(d) for d in old_list]
            else:
                merged_list = old_list

            setattr(old_award, attr, merged_list)

        return old_award
