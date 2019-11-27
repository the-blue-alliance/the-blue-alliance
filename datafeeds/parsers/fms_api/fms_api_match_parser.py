import datetime
import json
import logging

from google.appengine.ext import ndb

from consts.playoff_type import PlayoffType
from helpers.match_helper import MatchHelper
from helpers.playoff_advancement_helper import PlayoffAdvancementHelper
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


class FMSAPIHybridScheduleParser(object):

    def __init__(self, year, event_short):
        self.year = year
        self.event_short = event_short

    @classmethod
    def is_blank_match(cls, match):
        """
        Detect junk playoff matches like in 2017scmb
        """
        if match.comp_level == 'qm' or not match.score_breakdown:
            return False
        for color in ['red', 'blue']:
            if match.alliances[color]['score'] != 0:
                return False
            for value in match.score_breakdown[color].values():
                if value and value not in  {'Unknown', 'None'}:  # Nonzero, False, blank, None, etc.
                    return False
        return True

    def parse(self, response):
        import pytz

        matches = response['Schedule']

        event_key = '{}{}'.format(self.year, self.event_short)
        event = Event.get_by_id(event_key)
        if event.timezone_id:
            event_tz = pytz.timezone(event.timezone_id)
        else:
            logging.warning("Event {} has no timezone! Match times may be wrong.".format(event_key))
            event_tz = None

        parsed_matches = []
        remapped_matches = {}  # If a key changes due to a tiebreaker
        for match in matches:
            if 'tournamentLevel' in match:  # 2016+
                level = match['tournamentLevel']
            else:  # 2015
                level = match['level']
            comp_level = PlayoffType.get_comp_level(event.playoff_type, level, match['matchNumber'])
            set_number, match_number = PlayoffType.get_set_match_number(event.playoff_type, comp_level, match['matchNumber'])

            red_teams = []
            blue_teams = []
            red_surrogates = []
            blue_surrogates = []
            red_dqs = []
            blue_dqs = []
            team_key_names = []
            null_team = False
            sorted_teams = sorted(match.get('teams', match.get('Teams', [])), key=lambda team: team['station'])  # Sort by station to ensure correct ordering. Kind of hacky.
            for team in sorted_teams:
                if team['teamNumber'] is None:
                    null_team = True
                team_key = 'frc{}'.format(team['teamNumber'])
                team_key_names.append(team_key)
                if 'Red' in team['station']:
                    red_teams.append(team_key)
                    if team['surrogate']:
                        red_surrogates.append(team_key)
                    if team['dq']:
                        red_dqs.append(team_key)
                elif 'Blue' in team['station']:
                    blue_teams.append(team_key)
                    if team['surrogate']:
                        blue_surrogates.append(team_key)
                    if team['dq']:
                        blue_dqs.append(team_key)

            if null_team and match['scoreRedFinal'] is None and match['scoreBlueFinal'] is None:
                continue

            alliances = {
                'red': {
                    'teams': red_teams,
                    'surrogates': red_surrogates,
                    'dqs': red_dqs,
                    'score': match['scoreRedFinal']
                },
                'blue': {
                    'teams': blue_teams,
                    'surrogates': blue_surrogates,
                    'dqs': blue_dqs,
                    'score': match['scoreBlueFinal']
                },
            }

            if not match['startTime']:  # no startTime means it's an unneeded rubber match
                continue

            time = datetime.datetime.strptime(match['startTime'].split('.')[0], TIME_PATTERN)
            if event_tz is not None:
                time = time - event_tz.utcoffset(time)

            actual_time_raw = match['actualStartTime'] if 'actualStartTime' in match else None
            actual_time = None
            if actual_time_raw is not None:
                actual_time = datetime.datetime.strptime(actual_time_raw.split('.')[0], TIME_PATTERN)
                if event_tz is not None:
                    actual_time = actual_time - event_tz.utcoffset(actual_time)

            post_result_time_raw = match.get('postResultTime')
            post_result_time = None
            if post_result_time_raw is not None:
                post_result_time = datetime.datetime.strptime(post_result_time_raw.split('.')[0], TIME_PATTERN)
                if event_tz is not None:
                    post_result_time = post_result_time - event_tz.utcoffset(post_result_time)

            key_name = Match.renderKeyName(
                event_key,
                comp_level,
                set_number,
                match_number)

            # Check for tiebreaker matches
            existing_match = Match.get_by_id(key_name)
            # Follow chain of existing matches
            while existing_match is not None and existing_match.tiebreak_match_key is not None:
                logging.info("Following Match {} to {}".format(existing_match.key.id(), existing_match.tiebreak_match_key.id()))
                existing_match = existing_match.tiebreak_match_key.get()
            # Check if last existing match needs to be tiebroken
            if existing_match and existing_match.comp_level != 'qm' and \
                    existing_match.has_been_played and \
                    existing_match.winning_alliance == '' and \
                    existing_match.actual_time != actual_time and \
                    not self.is_blank_match(existing_match):
                logging.warning("Match {} is tied!".format(existing_match.key.id()))

                # TODO: Only query within set if set_number ever gets indexed
                match_count = 0
                for match_key in Match.query(Match.event==event.key, Match.comp_level==comp_level).fetch(keys_only=True):
                    _, match_key = match_key.id().split('_')
                    if match_key.startswith('{}{}'.format(comp_level, set_number)):
                        match_count += 1

                # Sanity check: Tiebreakers must be played after at least 3 matches if not finals
                if match_count < 3 and comp_level != 'f':
                    logging.warning("Match supposedly tied, but existing count is {}! Skipping match.".format(match_count))
                    continue

                match_number = match_count + 1
                new_key_name = Match.renderKeyName(
                    event_key,
                    comp_level,
                    set_number,
                    match_number)
                remapped_matches[key_name] = new_key_name
                key_name = new_key_name

                # Point existing match to new tiebreaker match
                existing_match.tiebreak_match_key = ndb.Key(Match, key_name)
                parsed_matches.append(existing_match)

                logging.warning("Creating new match: {}".format(key_name))
            elif existing_match:
                remapped_matches[key_name] = existing_match.key.id()
                key_name = existing_match.key.id()
                match_number = existing_match.match_number

            parsed_matches.append(Match(
                id=key_name,
                event=event.key,
                year=event.year,
                set_number=set_number,
                match_number=match_number,
                comp_level=comp_level,
                team_key_names=team_key_names,
                time=time,
                actual_time=actual_time,
                post_result_time=post_result_time,
                alliances_json=json.dumps(alliances),
            ))

        if self.year == 2015:
            # Fix null teams in elims (due to FMS API failure, some info not complete)
            # Should only happen for sf and f matches
            organized_matches = MatchHelper.organizeMatches(parsed_matches)
            for level in ['sf', 'f']:
                playoff_advancement = PlayoffAdvancementHelper.generatePlayoffAdvancement2015(organized_matches)
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

        return parsed_matches, remapped_matches


class FMSAPIMatchDetailsParser(object):
    def __init__(self, year, event_short):
        self.year = year
        self.event_short = event_short

    def parse(self, response):
        matches = response['MatchScores']

        event_key = '{}{}'.format(self.year, self.event_short)
        event = Event.get_by_id(event_key)

        match_details_by_key = {}

        for match in matches:
            comp_level = PlayoffType.get_comp_level(event.playoff_type, match['matchLevel'], match['matchNumber'])
            set_number, match_number = PlayoffType.get_set_match_number(event.playoff_type, comp_level, match['matchNumber'])
            breakdown = {
                'red': {},
                'blue': {},
            }
            if 'coopertition' in match:
                breakdown['coopertition'] = match['coopertition']
            if 'coopertitionPoints' in match:
                breakdown['coopertition_points'] = match['coopertitionPoints']

            game_data = None
            if self.year == 2018:
                # Switches should be the same, but parse individually in case FIRST change things
                right_switch_red = match['switchRightNearColor'] == 'Red'
                scale_red = match['scaleNearColor'] == 'Red'
                left_switch_red = match['switchLeftNearColor'] == 'Red'
                game_data = '{}{}{}'.format(
                    'L' if right_switch_red else 'R',
                    'L' if scale_red else 'R',
                    'L' if left_switch_red else 'R',
                )

            for alliance in match.get('alliances', match.get('Alliances', [])):
                color = alliance['alliance'].lower()
                for key, value in alliance.items():
                    if key != 'alliance':
                        breakdown[color][key] = value

                if game_data is not None:
                    breakdown[color]['tba_gameData'] = game_data

                if self.year == 2019:
                    # Derive incorrect completedRocketFar and completedRocketNear returns from FIRST API
                    for side1 in ['Near', 'Far']:
                        completedRocket = True
                        for side2 in ['Left', 'Right']:
                            for level in ['low', 'mid', 'top']:
                                if breakdown[color]['{}{}Rocket{}'.format(level, side2, side1)] != 'PanelAndCargo':
                                    completedRocket = False
                                    break
                            if not completedRocket:
                                break
                        breakdown[color]['completedRocket{}'.format(side1)] = completedRocket

            match_details_by_key[Match.renderKeyName(
                '{}{}'.format(self.year, self.event_short),
                comp_level,
                set_number,
                match_number)] = breakdown

        return match_details_by_key
