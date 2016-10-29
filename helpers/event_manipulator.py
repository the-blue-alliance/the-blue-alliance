import logging
import traceback

from google.appengine.api import search, taskqueue
from google.appengine.ext import ndb

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
            lat_lon = EventHelper.get_lat_lon(event.location)
            if not lat_lon:
                logging.warning("Lat/Lon update for event {} failed!".format(event.key_name))
            else:
                event.lat_lon = ndb.GeoPt(lat_lon[0], lat_lon[1])
                timezone_id = EventHelper.get_timezone_id(event.location, lat_lon=lat_lon)
                if not timezone_id:
                    logging.warning("Timezone update for event {} failed!".format(event.key_name))
                else:
                    event.timezone_id = timezone_id
                cls.createOrUpdate(event, run_post_update_hook=False)

        # Enqueue task to calculate district points
        for event in events:
            taskqueue.add(
                url='/tasks/math/do/district_points_calc/{}'.format(event.key.id()),
                method='GET')

        # Add event to lat/lon info to search index
        for event in events:
            if event.lat_lon:
                fields = [
                    search.NumberField(name='year', value=event.year),
                    search.GeoField(name='location', value=search.GeoPoint(event.lat_lon.lat, event.lat_lon.lon))
                ]
                search.Index(name="eventLocation").put(search.Document(doc_id=event.key.id(), fields=fields))

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
            "custom_hashtag",
            "facebook_eid",
            "first_eid",
            "city",
            "state_prov",
            "country",
            "postalcode",
            "lat_lon",
            "timezone_id",
            "name",
            "official",
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
