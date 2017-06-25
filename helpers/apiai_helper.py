import datetime

from database.event_query import TeamYearEventsQuery
from helpers.event_team_status_helper import EventTeamStatusHelper
from models.event_team import EventTeam
from models.team import Team


class APIAIHelper(object):
    ACTION_MAP = {
        'getteam.generic': '_getteam_generic',
        'getteam.location': '_getteam_location',
        'getteam.rookieyear': '_getteam_rookieyear',
        'getteam.status': '_getteam_status',
    }

    @classmethod
    def process_request(cls, request):
        action = request['result']['action']
        parameters = request['result']['parameters']

        return getattr(APIAIHelper, cls.ACTION_MAP.get(action, '_unknown_action'))(parameters)

    @classmethod
    def _team_number_tts(cls, team_number):
        team_number = int(team_number)
        if team_number < 10:
            return team_number
        if team_number % 100 == 0:
            return team_number

        team_number_str = str(team_number)
        if len(team_number_str) % 2 == 0:
            tts = ''
            start_idx = 0
        else:
            tts = '{} '.format(team_number_str[0])
            start_idx = 1

        return tts + ' '.join([team_number_str[i:i+2] for i in range(start_idx, len(team_number_str), 2)])

    @classmethod
    def _create_simple_response(cls, display_text, tts=None):
        return [{
            'type': 0,
            'speech': display_text,
        },
        {
            'type': 'simple_response',
            'platform': 'google',
            'displayText': display_text,
            'textToSpeech': tts if tts else display_text,
        }]

    # Currently Unused
    # @classmethod
    # def _create_basic_card(cls, title, subtitle, buttons):
    #     return [{
    #         'type': 'basic_card',
    #         'platform': 'google',
    #         'title': title,
    #         'subtitle': subtitle,
    #         'formattedText': text,  # Only required field
    #         'image': {
    #             'url': image_url,
    #         },
    #         'buttons': [
    #             {
    #                 'title': link_title,
    #                 'openUrlAction': {
    #                     'url': link_url,
    #                 }
    #             }
    #         ],
    #     }]

    @classmethod
    def _create_suggestion_chips(cls, suggestions):
        return [{
            'type': 'suggestion_chips',
            'platform': 'google',
            'suggestions': [{'title': suggestion} for suggestion in suggestions]
        }]

    @classmethod
    def _create_link_chip(cls, text, url):
        return [{
            'type': 'link_out_chip',
            'platform': 'google',
            'destinationName': text,
            'url': url,
        }]

    @classmethod
    def _unknown_action(cls, parameters):
        text = 'Whoops, something went wrong. Please ask me something else.'
        return {
            'speech': text,
            'messages': cls._create_simple_response(text)
        }

    @classmethod
    def _getteam_generic(cls, parameters):
        team_number = parameters['team_number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            text = 'What would you like to know about Team {0}? You can ask about their location, rookie year, or current status.'.format(
                team_number, team.city_state_country)
            tts = 'What would you like to know about Team {0}? You can ask about their location, rookie year, or current status.'.format(
                cls._team_number_tts(team_number), team.city_state_country)
        else:
            text = 'Team {0} does not exist. Please ask about another team.'.format(team_number)
            tts = 'Team {0} does not exist. Please ask about another team.'.format(cls._team_number_tts(team_number))

        return {
            'speech': text,
            'messages': cls._create_simple_response(text, tts=tts) +
                cls._create_suggestion_chips([
                    'Location',
                    'Rookie year',
                    'Current status'
                ])
        }

    @classmethod
    def _getteam_location(cls, parameters):
        team_number = parameters['team_number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            text = 'Team {0} is from {1}. Would you like to know more about {0} or another team?'.format(
                team_number, team.city_state_country)
            tts = 'Team {0} is from {1}. Would you like to know more about {0} or another team?'.format(
                cls._team_number_tts(team_number), team.city_state_country)
            messages = cls._create_simple_response(text, tts=tts) + \
                cls._create_suggestion_chips([
                    'Rookie year',
                    'Current status',
                    'Another team'
                ])
        else:
            text = 'Team {0} does not exist. Please ask about another team.'.format(team_number)
            tts = 'Team {0} does not exist. Please ask about another team.'.format(cls._team_number_tts(team_number))
            messages = cls._create_simple_response(text, tts=tts)

        return {
            'speech': text,
            'messages': messages,
        }

    @classmethod
    def _getteam_rookieyear(cls, parameters):
        team_number = parameters['team_number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            text = 'Team {0} first competed in {1}. Would you like to know more about {0} or another team?'.format(
                team_number, team.rookie_year)
            tts = 'Team {0} first competed in {1}. Would you like to know more about {0} or another team?'.format(
                cls._team_number_tts(team_number), team.rookie_year)
            messages = cls._create_simple_response(text, tts=tts) + \
                cls._create_suggestion_chips([
                    'Location',
                    'Current status',
                    'Another team'
                ])
        else:
            text = 'Team {0} does not exist. Please ask about another team.'.format(team_number)
            tts = 'Team {0} does not exist. Please ask about another team.'.format(cls._team_number_tts(team_number))
            messages = cls._create_simple_response(text, tts=tts)

        return {
            'speech': text,
            'messages': messages,
        }

    @classmethod
    def _getteam_status(cls, parameters):
        team_number = parameters['team_number']
        team_key = 'frc{}'.format(team_number)
        team = Team.get_by_id(team_key)
        if team:
            events = TeamYearEventsQuery(team_key, datetime.datetime.now().year).fetch()
            current_event = None
            for event in events:
                if event.now:
                    current_event = event

            if current_event:
                event_team = EventTeam.get_by_id('{}_{}'.format(current_event.key.id(), team_key))

                text = EventTeamStatusHelper.generate_team_at_event_status_string(team_key, event_team.status, formatting=False, event=current_event)
                tts = 'Team {} {}'.format(cls._team_number_tts(team_number), EventTeamStatusHelper.generate_team_at_event_status_string(team_key, event_team.status, formatting=False, event=current_event, include_team=False, verbose=True))

                additional_prompt = ' Would you like to know more about {} or another team?'.format(team_number)
                text += additional_prompt
                tts += additional_prompt

                messages = cls._create_simple_response(text, tts=tts) +\
                    cls._create_link_chip(event.display_name, 'https://www.thebluealliance.com/event/{}'.format(event.key.id()))
            else:
                text = 'Team {0} is not currently competing. Would you like to know more about {0} or another team?'.format(
                    team_number)
                tts = 'Team {0} is not currently competing. Would you like to know more about {0} or another team?'.format(
                    cls._team_number_tts(team_number))
                messages = cls._create_simple_response(text, tts=tts)

            messages += cls._create_suggestion_chips([
                    'Location',
                    'Rookie year',
                    'Another team'
                ])
        else:
            text = 'Team {0} does not exist. Please ask about another team.'.format(team_number)
            tts = 'Team {0} does not exist. Please ask about another team.'.format(cls._team_number_tts(team_number))
            messages = cls._create_simple_response(text, tts=tts)

        return {
            'speech': text,
            'messages': messages,
        }
