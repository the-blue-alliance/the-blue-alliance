import datetime
import json
import logging
import pytz

from helpers.match_helper import MatchHelper
from models.event import Event
from models.match import Match

QF_SF_MAP = {
    1: (1, 3),  # in sf1, qf seeds 2 and 4 play. 0-indexed becomes 1, 3
    2: (0, 2),
    3: (1, 2),
    4: (0, 3),
    5: (2, 3),
    6: (0, 1)
}

LAST_LEVEL = {
    'sf': 'qf',
    'f': 'sf'
}


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
        event = Event.get_by_id(event_key)
        if event.timezone_id:
            event_tz = pytz.timezone(event.timezone_id)
        else:
            logging.warning("Event {} has no timezone! Match times may be wrong.").format(event_key)
            event_tz = None

        set_number = 1
        parsed_matches = []
        for match in matches:
            comp_level = self._get_comp_level(match['level'], match['matchNumber'])
            match_number = self._get_match_number(comp_level, match['matchNumber'])

            red_teams = []
            blue_teams = []
            team_key_names = []
            null_team = False
            for team in match['Teams']:
                if team['teamNumber'] is None:
                    null_team = True
                team_key = 'frc{}'.format(team['teamNumber'])
                team_key_names.append(team_key)
                if 'Red' in team['station']:
                    red_teams.append(team_key)
                elif 'Blue' in team['station']:
                    blue_teams.append(team_key)
            if null_team and match['scoreRedFinal'] is None and match['scoreBlueFinal'] is None:
                continue

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

            time = datetime.datetime.strptime(match['startTime'], "%Y-%m-%dT%H:%M:%S")
            if event_tz is not None:
                time = time - event_tz.utcoffset(time)

            parsed_matches.append(Match(
                id=Match.renderKeyName(
                    event_key,
                    comp_level,
                    set_number,
                    match_number),
                event=event.key,
                game="frc_unknown",  # TODO: deprecate in favor of a 'year' property
                set_number=set_number,
                match_number=match_number,
                comp_level=comp_level,
                team_key_names=team_key_names,
                time=time,
                alliances_json=json.dumps(alliances),
                score_breakdown_json=json.dumps(score_breakdown)
            ))

        # Fix null teams in elims (due to FMS API failure, some info not complete)
        # Should only happen for sf and f matches
        organized_matches = MatchHelper.organizeMatches(parsed_matches)
        for level in ['sf', 'f']:
            playoff_advancement = MatchHelper.generatePlayoffAdvancement2015(organized_matches)
            if playoff_advancement[LAST_LEVEL[level]] != []:
                for match in organized_matches[level]:
                    if 'frcNone' in match.team_key_names:
                        if level == 'sf':
                            red_seed, blue_seed = QF_SF_MAP[match.match_number]
                        else:
                            red_seed = 0
                            blue_seed = 1
                        red_teams = ['frc{}'.format(t) for t in playoff_advancement[LAST_LEVEL[level]][red_seed][0]]
                        blue_teams = ['frc{}'.format(t) for t in playoff_advancement[LAST_LEVEL[level]][blue_seed][0]]

                        alliances = match.alliances
                        alliances['red']['teams'] = red_teams
                        alliances['blue']['teams'] = blue_teams
                        match.alliances_json = json.dumps(alliances)
                        match.team_key_names = red_teams + blue_teams

        fixed_matches = []
        for key, matches in organized_matches.items():
            if key != 'num':
                for match in matches:
                    if 'frcNone' not in match.team_key_names:
                        fixed_matches.append(match)

        return fixed_matches
