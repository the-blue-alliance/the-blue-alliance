from models.team import Team


class APIAIHelper(object):
    ACTION_MAP = {
        'getteam.rookieyear': '_getteam_rookieyear',
        'getteam.location': '_getteam_location',
    }

    @classmethod
    def process_request(cls, request):
        action = request['result']['action']
        parameters = request['result']['parameters']

        return getattr(APIAIHelper, cls.ACTION_MAP.get(action, '_unknown_action'))(parameters)

    @classmethod
    def _unknown_action(cls, parameters):
        message = 'Whoops, something went wrong. Please try again.'
        return {
            'speech': message,
            'messages': [
                {
                    'speech': message,
                    'type': 0,
                }
            ]
        }

    @classmethod
    def _getteam_location(cls, parameters):
        team_number = parameters['number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            message = 'Team {0} is from {1}. Would you like to know more about {0} or another team?'.format(
                team_number, team.city_state_country)
        else:
            message = 'Team {0} does not exist. Please ask about another team.'.format(team_number)

        return {
            'speech': message,
            'messages': [
                {
                    'speech': message,
                    'type': 0,
                }
            ]
        }

    @classmethod
    def _getteam_rookieyear(cls, parameters):
        team_number = parameters['number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            message = 'Team {0} first competed in {1}. Would you like to know more about {0} or another team?'.format(
                team_number, team.rookie_year)
        else:
            message = 'Team {0} does not exist. Please ask about another team.'.format(team_number)

        return {
            'speech': message,
            'messages': [
                {
                    'speech': message,
                    'type': 0,
                }
            ]
        }
