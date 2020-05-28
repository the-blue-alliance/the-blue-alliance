import json
import logging
import traceback

from google.appengine.ext import ndb

from helpers.cache_clearer import CacheClearer
from helpers.location_helper import LocationHelper
from helpers.manipulator_base import ManipulatorBase
from helpers.notification_helper import NotificationHelper
from helpers.search_helper import SearchHelper


class EventManipulator(ManipulatorBase):
    """
    Handle Event database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_event_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postDeleteHook(cls, events):
        '''
        To run after the event has been deleted.
        '''
        for event in events:
            SearchHelper.remove_event_location_index(event)

    @classmethod
    def postUpdateHook(cls, events, updated_attr_list, is_new_list):
        """
        To run after models have been updated
        """
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

    @classmethod
    def updateMerge(self, new_event, old_event, auto_union=True):
        """
        Given an "old" and a "new" Event object, replace the fields in the
        "old" event that are present in the "new" event, but keep fields from
        the "old" event that are null in the "new" event.
        """
        attrs = [
            "end_date",
            "event_short",
            "event_type_enum",
            "event_district_enum",
            "district_key",
            "custom_hashtag",
            "enable_predictions",
            "facebook_eid",
            "first_code",
            "first_eid",
            "city",
            "state_prov",
            "country",
            "postalcode",
            "parent_event",
            "playoff_type",
            "normalized_location",  # Overwrite whole thing as one
            "timezone_id",
            "name",
            "official",
            "short_name",
            "start_date",
            "venue",
            "venue_address",
            "website",
            "year",
            "remap_teams",
        ]

        allow_none_attrs = {
            'district_key'
        }

        list_attrs = [
            "divisions",
        ]

        old_event._updated_attrs = []

        for attr in attrs:
            if getattr(new_event, attr) is not None or attr in allow_none_attrs:
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

        # Special case to handle webcast_json
        if not auto_union and new_event.webcast != old_event.webcast:
            old_event.webcast_json = new_event.webcast_json
            old_event.dirty = True
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
                old_event.dirty = True

        return old_event
