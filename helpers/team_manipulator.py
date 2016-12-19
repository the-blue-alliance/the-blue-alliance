import logging

from google.appengine.api import search

from helpers.cache_clearer import CacheClearer
from helpers.location_helper import LocationHelper
from helpers.manipulator_base import ManipulatorBase


class TeamManipulator(ManipulatorBase):
    """
    Handle Team database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_team_cache_keys_and_controllers(affected_refs)

    # @classmethod
    # def postDeleteHook(cls, teams):
    #     '''
    #     To run after the team has been deleted.
    #     '''
    #     for team in teams:
    #         # Remove team from search index
    #         search.Index(name="teamLocation").delete(team.key.id())

    @classmethod
    def postUpdateHook(cls, teams, updated_attr_list, is_new_list):
        """
        To run after models have been updated
        """
        for (team, updated_attrs) in zip(teams, updated_attr_list):
            if set(['name', 'city', 'state_prov', 'country', 'postalcode']).intersection(set(updated_attrs)):
                LocationHelper.update_team_location(team)
                cls.createOrUpdate(team, run_post_update_hook=False)
            # lat_lon = team.get_lat_lon()
            # # Add team to lat/lon info to search index
            # if lat_lon:
            #     fields = [
            #         search.GeoField(name='location', value=search.GeoPoint(lat_lon[0], lat_lon[1]))
            #     ]
            #     search.Index(name="teamLocation").put(search.Document(doc_id=team.key.id(), fields=fields))

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
            "normalized_location",  # Overwrite whole thing as one
            "name",
            "nickname",
            "website",
            "rookie_year",
            "motto",
        ]
        old_team._updated_attrs = []

        for attr in attrs:
            if getattr(new_team, attr) is not None:
                if getattr(new_team, attr) != getattr(old_team, attr):
                    setattr(old_team, attr, getattr(new_team, attr))
                    old_team._updated_attrs.append(attr)
                    old_team.dirty = True

        # Take the new tpid and tpid_year iff the year is newer than the old one
        if (new_team.first_tpid_year > old_team.first_tpid_year):
            old_team.first_tpid_year = new_team.first_tpid_year
            old_team.first_tpid = new_team.first_tpid
            old_team._updated_attrs.append('first_tpid')
            old_team._updated_attrs.append('first_tpid_year')
            old_team.dirty = True

        return old_team
