import json

from google.appengine.ext import ndb

from models.media import Media
from models.team import Team
from consts.media_type import MediaType
from helpers.media_manipulator import MediaManipulator


class FMSAPITeamAvatarParser(object):
    def __init__(self, year,  short=None):
        self.year = year
        self.event_short = short

    def parse(self, response):
        """
        Parse team avatar from FMSAPI
        """

        # Get team avatar
        current_page = response['pageCurrent']
        total_pages = response['pageTotal']
        teams = response['teams']
        avatars = []
        keys_to_delete = set()

        for teamData in teams:
            team_number = teamData['teamNumber']
            foreign_key = "avatar_{}_frc{}".format(self.year, team_number)
            media_key = ndb.Key('Media', Media.render_key_name(MediaType.AVATAR, foreign_key))

            if not teamData['encodedAvatar']:
                keys_to_delete.add(media_key)
                continue
            else:
                encoded_avatar = teamData['encodedAvatar']

            avatar = Media(
                key=media_key,
                details_json=json.dumps({'base64Image': encoded_avatar}),
                foreign_key=foreign_key,
                media_type_enum=MediaType.AVATAR,
                references=[ndb.Key('Team', "frc{}".format(team_number))],
                year=self.year
            )

            avatars.append(avatar)

        return (avatars, keys_to_delete, (current_page < total_pages))
