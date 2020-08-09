from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.district_team import DistrictTeam


class DistrictTeamManipulator(ManipulatorBase[DistrictTeam]):
    """
    Handle DistrictTeam database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_districtteam_cache_keys_and_controllers(affected_refs)
    """

    """
    @classmethod
    def postUpdateHook(cls, district_teams, updated_attr_list, is_new_list):
        '''
        To run after a district team has been updated.
        '''
        for (district_team, updated_attrs) in zip(district_teams, updated_attr_list):
            # Enqueue task to calculate district rankings
            try:
                taskqueue.add(
                    url='/tasks/math/do/district_rankings_calc/{}'.format(district_team.district_key.id()),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing district_rankings_calc for {}".format(district_team.district_key.id()))
                logging.error(traceback.format_exc())
    """

    @classmethod
    def updateMerge(
        cls,
        new_district_team: DistrictTeam,
        old_district_team: DistrictTeam,
        auto_union: bool = True,
    ) -> DistrictTeam:
        """
        Update and return DistrictTeams
        """
        cls._update_attrs(new_district_team, old_district_team, auto_union)
        return old_district_team
