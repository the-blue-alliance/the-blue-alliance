import logging

from google.appengine.api import search

from helpers.cache_clearer import CacheClearer
from helpers.event_helper import EventHelper
from helpers.manipulator_base import ManipulatorBase


class TeamManipulator(ManipulatorBase):
    """
    Handle Team database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_team_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postDeleteHook(cls, teams):
        '''
        To run after the team has been deleted.
        '''
        for team in teams:
            # Remove team from search index
            search.Index(name="teamLocation").delete(team.key.id())

    @classmethod
    def postUpdateHook(cls, teams, updated_attr_list, is_new_list):
        """
        To run after models have been updated
        """
        for (team, updated_attrs) in zip(teams, updated_attr_list):
            lat_lon = EventHelper.get_lat_lon('{}\n{}'.format(team.split_name[0], team.location))
            if not lat_lon:
                logging.warning("Finding Lat/Lon for team {} failed with split_name[0]! Trying again with location".format(team.key.id()))
                lat_lon = EventHelper.get_lat_lon('{}\n{}'.format(team.split_name[-1], team.location))
            if not lat_lon:
                logging.warning("Finding Lat/Lon for team {} failed with split_name[-1]! Trying again with location".format(team.key.id()))
                lat_lon = EventHelper.get_lat_lon(team.location)
            if not lat_lon:
                logging.warning("Finding Lat/Lon for tean {} failed with location!".format(team.key.id()))
            else:
                # Add team to lat/lon info to search index
                if lat_lon:
                    fields = [
                        search.GeoField(name='location', value=search.GeoPoint(lat_lon[0], lat_lon[1]))
                    ]
                    search.Index(name="teamLocation").put(search.Document(doc_id=team.key.id(), fields=fields))

    @classmethod
    def updateMerge(self, new_team, old_team, auto_union=True):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        attrs = [
            "city",
            "state_prov",
            "country",
            "postalcode",
            "name",
            "nickname",
            "website",
            "rookie_year",
            "motto",
        ]

        for attr in attrs:
            if getattr(new_team, attr) is not None:
                if getattr(new_team, attr) != getattr(old_team, attr):
                    setattr(old_team, attr, getattr(new_team, attr))
                    old_team.dirty = True

        # Take the new tpid and tpid_year iff the year is newer than the old one
        if (new_team.first_tpid_year > old_team.first_tpid_year):
            old_team.first_tpid_year = new_team.first_tpid_year
            old_team.first_tpid = new_team.first_tpid
            old_team.dirty = True

        return old_team
