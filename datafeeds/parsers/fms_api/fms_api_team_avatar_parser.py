from google.appengine.ext import ndb

from models.media import Media
from models.team import Team
from consts.media_type import MediaType
from helpers.media_manipulator import MediaManipulator


class FMSAPITeamAvatarParser(object):
    def __init__(self, year):
        self.year = year

    def parse(self, response):
        """
        Parse team avatar from FMSAPI
        """

        # Get team avatar
        current_page = response['pageCurrent']
        total_pages = response['pageTotal']
        teams = response['teams']
        ret_models = []
        media_to_put = []

        for teamData in teams:
            if teamData['encodedAvatar'] is u'':
                encoded_avatar = None
            else:
                encoded_avatar = teamData['encodedAvatar']

            team_key = "frc{}".format(teamData['teamNumber'])
            team_number = teamData['teamNumber']

            # team_reference = Media.create_reference('team', team_key)
            # temp = Media.create_reference('team', '2018_frc1741')

            media = Media(
                key=ndb.Key('Media', 'avatar_2018_frc1741'),
                details_json=u''.format(encoded_avatar),
                foreign_key=u'avatar_2018_frc1741',
                media_type_enum=MediaType.AVATAR,
                references=[ndb.Key('Team', 'frc1741')],
                year=2018
            )

            # media = Media(
            #     id=Media.render_key_name(MediaType.AVATAR, team_reference),
            #     foreign_key="{}".format(team_reference),
            #     media_type_enum=MediaType.AVATAR,
            #     details_json=None,
            #     private_details_json=None,
            #     year=self.year,
            #     references=[team_reference],
            #     preferred_references=[],
            # )
            media_to_put.append(media)

            team = Team(
                id=team_key,
                team_number=team_number,
                encoded_avatar=encoded_avatar
            )

            ret_models.append(team)

        MediaManipulator.createOrUpdate(media_to_put)

        return (ret_models, (current_page < total_pages))
