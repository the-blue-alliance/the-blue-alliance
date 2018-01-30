from models.team import Team


class FMSAPITeamAvatarParser(object):
    def __init__(self, year):
        self.year = year

    def parse(self, response):
        """
        Parse team avatar from FMSAPI
        """

        # Get team json
        # don't need to null check, if error, HTTP code != 200, so we wont' get here
        current_page = response['pageCurrent']
        total_pages = response['pageTotal']
        teams = response['teams']
        ret_models = []

        for teamData in teams:
            if teamData['encodedAvatar'] is u'':
                encoded_avatar = None
            else:
                encoded_avatar = teamData['encodedAvatar']

            team = Team(
                id="frc{}".format(teamData['teamNumber']),
                team_number=teamData['teamNumber'],
                encoded_avatar=encoded_avatar
            )

            ret_models.append(team)

        return (ret_models, (current_page < total_pages))
