import datetime
import json
import logging
import pytz
import re

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

TIME_PATTERN = "%Y-%m-%dT%H:%M:%S"

ELIM_MAPPING = {
    1: (1, 1),  # (set, match)
    2: (2, 1),
    3: (3, 1),
    4: (4, 1),
    5: (1, 2),
    6: (2, 2),
    7: (3, 2),
    8: (4, 2),
    9: (1, 3),
    10: (2, 3),
    11: (3, 3),
    12: (4, 3),
    13: (1, 1),
    14: (2, 1),
    15: (1, 2),
    16: (2, 2),
    17: (1, 3),
    18: (2, 3),
    19: (1, 1),
    20: (1, 2),
    21: (1, 3),
}


def get_comp_level(year, match_level, match_number):
    if match_level == 'Qualification':
        return 'qm'
    else:
        if year == 2015:
            if match_number <= 8:
                return 'qf'
            elif match_number <= 14:
                return 'sf'
            else:
                return 'f'
        else:
            if match_number <= 12:
                return 'qf'
            elif match_number <= 18:
                return 'sf'
            else:
                return 'f'


def get_set_match_number(year, comp_level, match_number):
    if year == 2015:
        if comp_level == 'sf':
            return 1, match_number - 8
        elif comp_level == 'f':
            return 1, match_number - 14
        else:  # qm, qf
            return 1, match_number
    else:
        if comp_level in {'qf', 'sf', 'f'}:
            return ELIM_MAPPING[match_number]
        else:  # qm
            return 1, match_number


class FMSAPIHybridScheduleParser(object):

    def __init__(self, year, event_short):
        self.year = year
        self.event_short = event_short

    def parse(self, response):
        matches = response['Schedule']

        event_key = '{}{}'.format(self.year, self.event_short)
        event = Event.get_by_id(event_key)
        if event.timezone_id:
            event_tz = pytz.timezone(event.timezone_id)
        else:
            logging.warning("Event {} has no timezone! Match times may be wrong.".format(event_key))
            event_tz = None

        parsed_matches = []
        for match in matches:
            if 'tournamentLevel' in match:  # 2016+
                level = match['tournamentLevel']
            else:  # 2015
                level = match['level']
            comp_level = get_comp_level(self.year, level, match['matchNumber'])
            set_number, match_number = get_set_match_number(self.year, comp_level, match['matchNumber'])

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

            time = datetime.datetime.strptime(match['startTime'].split('.')[0], TIME_PATTERN)
            actual_time_raw = match['actualStartTime'] if 'actualStartTime' in match else None
            actual_time = None
            if event_tz is not None:
                time = time - event_tz.utcoffset(time)

            if actual_time_raw is not None:
                actual_time = datetime.datetime.strptime(actual_time_raw.split('.')[0], TIME_PATTERN)
                if event_tz is not None:
                    actual_time = actual_time - event_tz.utcoffset(actual_time)

            parsed_matches.append(Match(
                id=Match.renderKeyName(
                    event_key,
                    comp_level,
                    set_number,
                    match_number),
                event=event.key,
                year=event.year,
                set_number=set_number,
                match_number=match_number,
                comp_level=comp_level,
                team_key_names=team_key_names,
                time=time,
                actual_time=actual_time,
                alliances_json=json.dumps(alliances),
            ))

        if self.year == 2015:
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
            parsed_matches = fixed_matches

        return parsed_matches


class FMSAPIMatchDetailsParser(object):
    def __init__(self, year, event_short):
        self.year = year
        self.event_short = event_short

    def parse(self, response):
        matches = response['MatchScores']

        match_details_by_key = {}
        for match in matches:
            comp_level = get_comp_level(self.year, match['matchLevel'], match['matchNumber'])
            set_number, match_number = get_set_match_number(self.year, comp_level, match['matchNumber'])
            breakdown = {
                'red': {},
                'blue': {},
            }
            if 'coopertition' in match:
                breakdown['coopertition'] = match['coopertition']
            if 'coopertitionPoints' in match:
                breakdown['coopertition_points'] = match['coopertitionPoints']
            for alliance in match['Alliances']:
                color = alliance['alliance'].lower()
                for key, value in alliance.items():
                    if key != 'alliance':
                        breakdown[color][key] = value

            match_details_by_key[Match.renderKeyName(
                '{}{}'.format(self.year, self.event_short),
                comp_level,
                set_number,
                match_number)] = breakdown

        return match_details_by_key
