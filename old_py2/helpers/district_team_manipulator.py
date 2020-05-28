from google.appengine.api import taskqueue
from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class DistrictTeamManipulator(ManipulatorBase):
    """
    Handle DistrictTeam database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_districtteam_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postUpdateHook(cls, district_teams, updated_attr_list, is_new_list):
        """
        To run after a district team has been updated.
        """
        for (district_team, updated_attrs) in zip(district_teams, updated_attr_list):
            # Enqueue task to calculate district rankings
            try:
                taskqueue.add(
                    url='/tasks/math/do/district_rankings_calc/{}'.format(district_team.district_key.id()),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing district_rankings_calc for {}".format(district_team.district_key.id()))
                logging.error(traceback.format_exc())

    @classmethod
    def updateMerge(self, new_district_team, old_district_team, auto_union=True):
        """
        Update and return DistrictTeams
        """
        immutable_attrs = [
            "team",
            "district",
            "year"
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "district_key",  # TEMPORARY, for migrations
        ]

        for attr in attrs:
            if getattr(new_district_team, attr) is not None:
                if getattr(new_district_team, attr) != getattr(old_district_team, attr):
                    setattr(old_district_team, attr, getattr(new_district_team, attr))
                    old_district_team.dirty = True

        return old_district_team
