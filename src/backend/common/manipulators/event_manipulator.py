import json

from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.event import Event


class EventManipulator(ManipulatorBase[Event]):
    """
    Handle Event database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_event_cache_keys_and_controllers(affected_refs)
    """

    """
    @classmethod
    def postDeleteHook(cls, events):
        '''
        To run after the event has been deleted.
        '''
        for event in events:
            SearchHelper.remove_event_location_index(event)
    """

    """
    @classmethod
    def postUpdateHook(cls, events, updated_attr_list, is_new_list):
        # To run after models have been updated
        for (event, updated_attrs) in zip(events, updated_attr_list):
            try:
                LocationHelper.update_event_location(event)
            except Exception, e:
                logging.error("update_event_location for {} errored!".format(event.key.id()))
                logging.exception(e)

            try:
                if event.normalized_location and event.normalized_location.lat_lng:
                    timezone_id = LocationHelper.get_timezone_id(
                        None, lat_lng=event.normalized_location.lat_lng)
                    if not timezone_id:
                        logging.warning("Timezone update for event {} failed!".format(event.key_name))
                    else:
                        event.timezone_id = timezone_id
                else:
                    logging.warning("No Lat/Lng to update timezone_id for event {}!".format(event.key_name))
            except Exception, e:
                logging.error("Timezone update for {} errored!".format(event.key.id()))
                logging.exception(e)

            try:
                SearchHelper.update_event_location_index(event)
            except Exception, e:
                logging.error("update_event_location_index for {} errored!".format(event.key.id()))
                logging.exception(e)
        cls.createOrUpdate(events, run_post_update_hook=False)
    """

    @classmethod
    def updateMerge(
        cls, new_event: Event, old_event: Event, auto_union: bool = True
    ) -> Event:
        cls._update_attrs(new_event, old_event, auto_union)

        # Special case to handle webcast_json
        if not auto_union and new_event.webcast != old_event.webcast:
            old_event.webcast_json = new_event.webcast_json
            old_event._webcast = None
            old_event._dirty = True
        else:
            if new_event.webcast:
                old_webcasts = old_event.webcast
                if old_webcasts:
                    for webcast in new_event.webcast:
                        if webcast in old_webcasts:
                            continue
                        else:
                            old_webcasts.append(webcast)
                            old_event.webcast_json = json.dumps(old_webcasts)
                else:
                    old_event.webcast_json = new_event.webcast_json
                old_event._dirty = True

        return old_event
