import datetime
import json

from google.appengine.ext import ndb

from models.event import Event
from models.match import Match


class FMSAPIHybridScheduleParser(object):
    def __init__(self, year, event_short):
        self.year = year
        self.event_short = event_short

    def _get_comp_level(self, match_level, match_number):
        if match_level == 'Qualification':
            return 'qm'
        else:
            if match_number <= 8:
                return 'qf'
            elif match_number <= 14:
                return 'sf'
            else:
                return 'f'

    def _get_match_number(self, comp_level, match_number):
        if comp_level == 'sf':
            return match_number - 8
        elif comp_level == 'f':
            return match_number - 14
        else:  # qm, qf
            return match_number

    def parse(self, response):
        """
        This currently only works for the 2015 game, where elims matches are all part of one set.
        """
        matches = response['Schedule']

        event_key = '{}{}'.format(self.year, self.event_short)
        set_number = 1
        parsed_matches = []
        for match in matches:
            comp_level = self._get_comp_level(match['level'], match['matchNumber'])

            red_teams = []
            blue_teams = []
            team_key_names = []
            for team in match['Teams']:
                team_key = 'frc{}'.format(team['teamNumber'])
                team_key_names.append(team_key)
                if 'Red' in team['station']:
                    red_teams.append(team_key)
                elif 'Blue' in team['station']:
                    blue_teams.append(team_key)

            alliances = {
                'red': {
                    'teams': red_teams,
                    'score': match['scoreRedFinal']
                },
                'blue': {
                    'teams': blue_teams,
                    'score': match['scoreBlueFinal']
                }
            }

            score_breakdown = {
                'red': {
                    'auto': match['scoreRedAuto'],
                    'foul': match['scoreRedFoul']
                },
                'blue': {
                    'auto': match['scoreBlueAuto'],
                    'foul': match['scoreBlueFoul']
                }
            }

            parsed_matches.append(Match(
                id=Match.renderKeyName(
                    event_key,
                    comp_level,
                    set_number,
                    match['matchNumber']),
                event=ndb.Key(Event, event_key),
                game="frc_unknown",  # TODO: deprecate in favor of a 'year' property
                set_number=set_number,
                match_number=self._get_match_number(comp_level, match['matchNumber']),
                comp_level=comp_level,
                team_key_names=team_key_names,
                time=datetime.datetime.strptime(match['startTime'], "%Y-%m-%dT%H:%M:%S"),
                alliances_json=json.dumps(alliances),
                score_breakdown_json=json.dumps(score_breakdown)
            ))

        return parsed_matches
