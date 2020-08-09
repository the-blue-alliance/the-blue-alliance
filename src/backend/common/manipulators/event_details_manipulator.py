from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.event_details import EventDetails


class EventDetailsManipulator(ManipulatorBase[EventDetails]):
    """
    Handle EventDetails database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_event_details_cache_keys_and_controllers(affected_refs)
    """

    """ndb
    @classmethod
    def postUpdateHook(cls, event_details_list, updated_attr_list, is_new_list):
        '''
        To run after models have been updated
        '''
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
    """

    @classmethod
    def updateMerge(
        cls,
        new_event_details: EventDetails,
        old_event_details: EventDetails,
        auto_union: bool = True,
    ) -> EventDetails:
        cls._update_attrs(new_event_details, old_event_details, auto_union)
        return old_event_details
