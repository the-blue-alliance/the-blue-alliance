import datetime

from database.event_query import TeamYearEventsQuery
from database.match_query import TeamEventMatchesQuery
from helpers.event_helper import EventHelper
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.match_helper import MatchHelper
from models.event_team import EventTeam
from models.team import Team


class APIAIHelper(object):
    ACTION_MAP = {
        'getteam.generic': '_getteam_generic',
        'getteam.fallback': '_getteam_fallback',
        'getteam.location': '_getteam_location',
        'getteam.rookieyear': '_getteam_rookieyear',
        'getteam.status': '_getteam_status',
        'getteam.nextmatch': '_getteam_nextmatch',
    }

    @classmethod
    def process_request(cls, request):
        action = request['result']['action']
        return getattr(APIAIHelper, cls.ACTION_MAP.get(action, '_unknown_action'))(request)

    @classmethod
    def _team_number_tts(cls, team_number):
        if not team_number.isdigit():  # For handling invalid team numbers
            return team_number

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
    def _unknown_action(cls, request):
        text = 'Whoops, something went wrong. Please ask me something else.'
        return {
            'speech': text,
            'messages': cls._create_simple_response(text)
        }

    @classmethod
    def _getteam_generic(cls, request):
        team_number = request['result']['parameters']['team_number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            fmt = 'What would you like to know about Team {0}? I can tell you about their next match, how they are currently doing, or generic information like their location or rookie year.'
            add_messages = cls._create_suggestion_chips([
                'Next match',
                'Current status',
                'Location',
                'Rookie year',
            ])
        else:
            fmt = 'Team {0} does not exist. Please ask about another team.'
            add_messages = []
        text = fmt.format(team_number)
        tts = fmt.format(cls._team_number_tts(team_number))

        return {
            'speech': text,
            'messages': cls._create_simple_response(text, tts=tts) + add_messages
        }

    @classmethod
    def _getteam_fallback(cls, request):
        team_number = None
        for context in request['result']['contexts']:
            if context['name'] == 'getteam':
                team_number = context['parameters']['team_number']
                break
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            fmt = 'Sorry, I don\'t understand your question about Team {0}. Try asking about their next match, status, location, or rookie year.'
        else:
            fmt = 'Team {0} does not exist. Please ask about another team.'
        text = fmt.format(team_number)
        tts = fmt.format(cls._team_number_tts(team_number))

        return {
            'speech': text,
            'messages': cls._create_simple_response(text, tts=tts) +
                cls._create_suggestion_chips([
                    'Next match',
                    'Current status',
                    'Location',
                    'Rookie year',
                ])
        }

    @classmethod
    def _getteam_location(cls, request):
        team_number = request['result']['parameters']['team_number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            fmt = 'Team {0} is from {1}. Would you like to know more about {0} or another team?'
            text = fmt.format(
                team_number, team.city_state_country)
            tts = fmt.format(
                cls._team_number_tts(team_number), team.city_state_country)
            messages = cls._create_simple_response(text, tts=tts) + \
                cls._create_suggestion_chips([
                    'Next match',
                    'Current status',
                    'Rookie year',
                    'Another team',
                    'No thanks',
                ])
        else:
            fmt = 'Team {0} does not exist. Please ask about another team.'
            text = fmt.format(team_number)
            tts = fmt.format(cls._team_number_tts(team_number))
            messages = cls._create_simple_response(text, tts=tts)

        return {
            'speech': text,
            'messages': messages,
        }

    @classmethod
    def _getteam_rookieyear(cls, request):
        team_number = request['result']['parameters']['team_number']
        team = Team.get_by_id('frc{}'.format(team_number))
        if team:
            fmt = 'Team {0} first competed in {1}. Would you like to know more about {0} or another team?'
            text = fmt.format(
                team_number, team.rookie_year)
            tts = fmt.format(
                cls._team_number_tts(team_number), team.rookie_year)
            messages = cls._create_simple_response(text, tts=tts) + \
                cls._create_suggestion_chips([
                    'Next match',
                    'Current status',
                    'Location',
                    'Another team',
                    'No thanks',
                ])
        else:
            fmt = 'Team {0} does not exist. Please ask about another team.'
            text = fmt.format(team_number)
            tts = fmt.format(cls._team_number_tts(team_number))
            messages = cls._create_simple_response(text, tts=tts)

        return {
            'speech': text,
            'messages': messages,
        }

    @classmethod
    def _getteam_status(cls, request):
        team_number = request['result']['parameters']['team_number']
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

                text = EventTeamStatusHelper.generate_team_at_event_status_string(
                    team_key, event_team.status, formatting=False, event=current_event)
                tts = 'Team {} {}'.format(
                    cls._team_number_tts(team_number),
                    EventTeamStatusHelper.generate_team_at_event_status_string(
                        team_key, event_team.status, formatting=False, event=current_event, include_team=False, verbose=True))

                additional_prompt = ' Would you like to know more about {} or another team?'.format(team_number)
                text += additional_prompt
                tts += additional_prompt

                messages = cls._create_simple_response(text, tts=tts) +\
                    cls._create_link_chip(current_event.display_name, 'https://www.thebluealliance.com/event/{}'.format(current_event.key.id()))
            else:
                fmt = 'Team {0} is not currently competing. Would you like to know more about {0} or another team?'
                text = fmt.format(
                    team_number)
                tts = fmt.format(
                    cls._team_number_tts(team_number))
                messages = cls._create_simple_response(text, tts=tts)

            messages += cls._create_suggestion_chips([
                    'Next match',
                    'Location',
                    'Rookie year',
                    'Another team',
                    'No thanks',
                ])
        else:
            fmt = 'Team {0} does not exist. Please ask about another team.'
            text = fmt.format(team_number)
            tts = fmt.format(cls._team_number_tts(team_number))
            messages = cls._create_simple_response(text, tts=tts)

        return {
            'speech': text,
            'messages': messages,
        }

    @classmethod
    def _getteam_nextmatch(cls, request):
        team_number = request['result']['parameters']['team_number']
        team_key = 'frc{}'.format(team_number)
        team = Team.get_by_id(team_key)
        if team:
            events = TeamYearEventsQuery(team_key, datetime.datetime.now().year).fetch()
            EventHelper.sort_events(events)

            # Find first current or future event
            for event in events:
                if event.now:
                    matches = TeamEventMatchesQuery(team_key, event.key.id()).fetch()
                    matches = MatchHelper.play_order_sort_matches(matches)
                    if matches:
                        next_match = None
                        for match in matches:
                            if not match.has_been_played:
                                next_match = match
                                break

                        if next_match is not None:
                            if match.predicted_time:
                                eta = match.predicted_time - datetime.datetime.now()
                                eta_str = None
                                if eta < datetime.timedelta(minutes=5):
                                    fmt = 'Team {0} will be playing in {1} soon at the {3}.'
                                else:
                                    eta_str = ''
                                    days = eta.days
                                    hours, rem = divmod(eta.seconds, 3600)
                                    minutes, _ = divmod(rem, 60)
                                    if days:
                                        eta_str += ' {} day{}'.format(days, '' if days == 1 else 's')
                                    if hours:
                                        eta_str += ' {} hour{}'.format(hours, '' if hours == 1 else 's')
                                    if minutes:
                                        eta_str += ' {} minute{}'.format(minutes, '' if minutes == 1 else 's')
                                    fmt = 'Team {0} will be playing in {1} in about{2} at the {3}.'
                                text = fmt.format(team_number, match.verbose_name, eta_str, event.normalized_name)
                                tts = fmt.format(cls._team_number_tts(team_number), match.verbose_name, eta_str, event.normalized_name)
                            else:
                                fmt = 'Team {0} will be playing in {1} at the {2}.'
                                text = fmt.format(team_number, match.verbose_name, event.normalized_name)
                                tts = fmt.format(cls._team_number_tts(team_number), match.verbose_name, event.normalized_name)
                            add_messages = cls._create_link_chip(
                                match.verbose_name,
                                'https://www.thebluealliance.com/match/{}'.format(match.key.id()))
                        else:
                            fmt = 'Team {0} has no more scheduled matches at the {1}.'
                            text = fmt.format(team_number, event.normalized_name)
                            tts = fmt.format(cls._team_number_tts(team_number), event.normalized_name)
                            add_messages = []
                    else:
                        fmt = 'Team {0} has no scheduled matches at the {1}.'
                        text = fmt.format(team_number, event.normalized_name)
                        tts = fmt.format(cls._team_number_tts(team_number), event.normalized_name)
                        add_messages = []
                    break
                elif event.future:
                    fmt = 'Team {0} will be competing at the {1} which begins on {2}.'
                    event_date = event.start_date.strftime("%B %d")
                    text = fmt.format(team_number, event.normalized_name, event_date)
                    tts = fmt.format(cls._team_number_tts(team_number), event.normalized_name, event_date)
                    add_messages = cls._create_link_chip(
                        'event page', 'https://www.thebluealliance.com/event/{}'.format(event.key.id()))
                    break
            else:
                fmt = 'Team {0} is not registered for any more events this season.'
                text = fmt.format(team_number)
                tts = fmt.format(cls._team_number_tts(team_number))
                add_messages = []

            fmt = ' Would you like to know more about {} or another team?'
            text += fmt.format(team_number)
            tts += fmt.format(cls._team_number_tts(team_number))
            add_messages += cls._create_suggestion_chips([
                'Current status',
                'Location',
                'Rookie year',
                'Another team',
                'No thanks',
            ])
        else:
            fmt = 'Team {0} does not exist. Please ask about another team.'
            text = fmt.format(team_number)
            tts = fmt.format(cls._team_number_tts(team_number))
            add_messages = []

        return {
            'speech': text,
            'messages': cls._create_simple_response(text, tts=tts) + add_messages,
        }
