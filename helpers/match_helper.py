import logging
from collections import defaultdict
import copy
import datetime
import json
import pytz
import re

from collections import defaultdict
from consts.event_type import EventType
from consts.playoff_type import PlayoffType

from helpers.match_manipulator import MatchManipulator

from models.match import Match


class MatchHelper(object):
    @classmethod
    def add_match_times(cls, event, matches):
        """
        Calculates and adds match times given an event and match time strings (from USFIRST)
        Assumes the last match is played on the last day of comeptition and
        works backwards from there.
        """
        if event.timezone_id is None:  # Can only calculate match times if event timezone is known
            logging.warning('Cannot compute match time for event with no timezone_id: {}'.format(event.key_name))
            return

        matches_reversed = cls.play_order_sort_matches(matches, reverse=True)
        tz = pytz.timezone(event.timezone_id)

        last_match_time = None
        cur_date = event.end_date + datetime.timedelta(hours=23, minutes=59, seconds=59)  # end_date is specified at midnight of the last day
        for match in matches_reversed:
            r = re.match(r'(\d+):(\d+) (am|pm)', match.time_string.lower())
            hour = int(r.group(1))
            minute = int(r.group(2))
            if hour == 12:
                hour = 0
            if r.group(3) == 'pm':
                hour += 12

            match_time = datetime.datetime(cur_date.year, cur_date.month, cur_date.day, hour, minute)
            if last_match_time is not None and last_match_time + datetime.timedelta(hours=6) < match_time:
                cur_date = cur_date - datetime.timedelta(days=1)
                match_time = datetime.datetime(cur_date.year, cur_date.month, cur_date.day, hour, minute)
            last_match_time = match_time

            match.time = match_time - tz.utcoffset(match_time)

    @classmethod
    def add_surrogates(cls, event):
        """
        If a team has more scheduled matches than other teams, then the third
        match is a surrogate.
        Valid for 2008 and up, don't compute for offseasons.
        """
        if event.year < 2008 or event.event_type_enum not in EventType.SEASON_EVENT_TYPES:
            return

        qual_matches = cls.organizeMatches(event.matches)['qm']
        if not qual_matches:
            return

        # Find surrogate teams
        match_counts = defaultdict(int)
        for match in qual_matches:
            for alliance_color in ['red', 'blue']:
                for team in match.alliances[alliance_color]['teams']:
                    match_counts[team] += 1
        num_matches = min(match_counts.values())
        surrogate_teams = set()
        for k, v in match_counts.items():
            if v > num_matches:
                surrogate_teams.add(k)

        # Add surrogate info
        num_played = defaultdict(int)
        for match in qual_matches:
            for alliance_color in ['red', 'blue']:
                match.alliances[alliance_color]['surrogates'] = []
                for team in match.alliances[alliance_color]['teams']:
                    num_played[team] += 1
                    if team in surrogate_teams and num_played[team] == 3:
                        match.alliances[alliance_color]['surrogates'].append(team)
            match.alliances_json = json.dumps(match.alliances)

        MatchManipulator.createOrUpdate(qual_matches)

    """
    Helper to put matches into sub-dictionaries for the way we render match tables
    """
    # Allows us to sort matches by key name.
    # Note: Matches within a comp_level (qual, qf, sf, f, etc.) will be in order,
    # but the comp levels themselves may not be in order. Doesn't matter because
    # XXX_match_table.html checks for comp_level when rendering the page
    @classmethod
    def natural_sort_matches(self, matches):
        import re
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda match: [convert(c) for c in re.split('([0-9]+)', str(match.key_name))]
        return sorted(matches, key=alphanum_key)

    @classmethod
    def play_order_sort_matches(self, matches, reverse=False):
        sort_key = lambda match: match.play_order
        return sorted(matches, key=sort_key, reverse=reverse)

    @classmethod
    def organizeMatches(self, match_list):
        match_list = MatchHelper.natural_sort_matches(match_list)
        matches = dict([(comp_level, list()) for comp_level in Match.COMP_LEVELS])
        matches["num"] = len(match_list)
        while len(match_list) > 0:
            match = match_list.pop(0)
            matches[match.comp_level].append(match)

        return matches

    @classmethod
    def organizeKeys(cls, match_keys):
        matches = dict([(comp_level, list()) for comp_level in Match.COMP_LEVELS])
        matches["num"] = len(match_keys)
        while len(match_keys) > 0:
            match_key = match_keys.pop(0)
            match_id = match_key.split("_")[1]
            for comp_level in Match.COMP_LEVELS:
                if match_id.startswith(comp_level):
                    matches[comp_level].append(match_key)

        return matches

    @classmethod
    def recentMatches(self, matches, num=3):
        matches = filter(lambda x: x.has_been_played, matches)
        matches = self.play_order_sort_matches(matches)
        return matches[-num:]

    @classmethod
    def upcomingMatches(self, matches, num=3):
        matches = self.play_order_sort_matches(matches)

        last_played_match_index = None
        for i, match in enumerate(reversed(matches)):
            if match.has_been_played:
                last_played_match_index = len(matches) - i
                break

        upcoming_matches = []
        for i, match in enumerate(matches[last_played_match_index:]):
            if i == num:
                break
            if not match.has_been_played:
                upcoming_matches.append(match)
        return upcoming_matches

    @classmethod
    def deleteInvalidMatches(self, match_list, event):
        """
        A match is invalid iff it is an elim match that has not been played
        and the same alliance already won in 2 match numbers in the same set.
        """
        red_win_counts = defaultdict(int)  # key: <comp_level><set_number>
        blue_win_counts = defaultdict(int)  # key: <comp_level><set_number>
        for match in match_list:
            if match.has_been_played and match.comp_level in Match.ELIM_LEVELS:
                key = '{}{}'.format(match.comp_level, match.set_number)
                if match.winning_alliance == 'red':
                    red_win_counts[key] += 1
                elif match.winning_alliance == 'blue':
                    blue_win_counts[key] += 1

        return_list = []
        for match in match_list:
            if match.comp_level in Match.ELIM_LEVELS and not match.has_been_played:
                if event.playoff_type != PlayoffType.ROUND_ROBIN_6_TEAM or match.comp_level == 'f':  # Don't delete round robin semifinal matches
                    key = '{}{}'.format(match.comp_level, match.set_number)
                    if red_win_counts[key] == 2 or blue_win_counts[key] == 2:
                        try:
                            MatchManipulator.delete(match)
                            logging.warning("Deleting invalid match: %s" % match.key_name)
                        except:
                            logging.warning("Tried to delete invalid match, but failed: %s" % match.key_name)
                        continue
            return_list.append(match)

        return return_list

    @classmethod
    def generateBracket(cls, matches, alliance_selections=None):
        complete_alliances = []
        bracket_table = defaultdict(lambda: defaultdict(dict))
        for comp_level in ['qf', 'sf', 'f']:
            for match in matches[comp_level]:
                set_number = match.set_number
                if set_number not in bracket_table[comp_level]:
                    bracket_table[comp_level][set_number] = {
                        'red_alliance': [],
                        'blue_alliance': [],
                        'winning_alliance': None,
                        'red_wins': 0,
                        'blue_wins': 0,
                    }
                for color in ['red', 'blue']:
                    alliance = copy.copy(match.alliances[color]['teams'])
                    for i, complete_alliance in enumerate(complete_alliances):  # search for alliance. could be more efficient
                        if len(set(alliance).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                            backups = list(set(alliance).difference(set(complete_alliance)))
                            complete_alliances[i] += backups  # ensures that backup robots are listed last

                            for team_num in cls.getOrderedAlliance(complete_alliances[i], alliance_selections):
                                if team_num not in bracket_table[comp_level][set_number]['{}_alliance'.format(color)]:
                                    bracket_table[comp_level][set_number]['{}_alliance'.format(color)].append(team_num)

                            break
                    else:
                        complete_alliances.append(alliance)

                winner = match.winning_alliance
                if not winner or winner == '':
                    # if the match is a tie
                    continue

                bracket_table[comp_level][set_number]['{}_wins'.format(winner)] = \
                    bracket_table[comp_level][set_number]['{}_wins'.format(winner)] + 1
                if bracket_table[comp_level][set_number]['red_wins'] == 2:
                    bracket_table[comp_level][set_number]['winning_alliance'] = 'red'
                if bracket_table[comp_level][set_number]['blue_wins'] == 2:
                    bracket_table[comp_level][set_number]['winning_alliance'] = 'blue'

        return bracket_table

    @classmethod
    def generatePlayoffAdvancement2015(cls, matches, alliance_selections=None):
        complete_alliances = []
        advancement = defaultdict(list)  # key: comp level; value: list of [complete_alliance, [scores], average_score]
        for comp_level in ['ef', 'qf', 'sf']:
            for match in matches.get(comp_level, []):
                if not match.has_been_played:
                    continue
                for color in ['red', 'blue']:
                    alliance = cls.getOrderedAlliance(match.alliances[color]['teams'], alliance_selections)
                    for i, complete_alliance in enumerate(complete_alliances):  # search for alliance. could be more efficient
                        if len(set(alliance).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                            backups = list(set(alliance).difference(set(complete_alliance)))
                            complete_alliances[i] += backups  # ensures that backup robots are listed last
                            break
                    else:
                        i = None
                        complete_alliances.append(alliance)

                    is_new = False
                    if i is not None:
                        for j, (complete_alliance, scores, _) in enumerate(advancement[comp_level]):  # search for alliance. could be more efficient
                            if len(set(complete_alliances[i]).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                                complete_alliance = complete_alliances[i]
                                scores.append(match.alliances[color]['score'])
                                advancement[comp_level][j][2] = float(sum(scores)) / len(scores)
                                break
                        else:
                            is_new = True

                    score = match.alliances[color]['score']
                    if i is None:
                        advancement[comp_level].append([alliance, [score], score])
                    elif is_new:
                        advancement[comp_level].append([complete_alliances[i], [score], score])

            advancement[comp_level] = sorted(advancement[comp_level], key=lambda x: -x[2])  # sort by descending average score

        return advancement

    @classmethod
    def generatePlayoffAdvancementRoundRobin(cls, matches, alliance_selections=None):
        complete_alliances = []
        alliance_names = []
        advancement = defaultdict(list)  # key: comp level; value: list of [complete_alliance, [champ_points], sum_champ_points, [match_points], sum_match_points
        for comp_level in ['sf']:  # In case this needs to scale to more levels
            any_unplayed = False
            for match in matches.get(comp_level, []):
                if not match.has_been_played:
                    any_unplayed = True
                for color in ['red', 'blue']:
                    alliance = cls.getOrderedAlliance(match.alliances[color]['teams'], alliance_selections)
                    alliance_name = cls.getAllianceName(match.alliances[color]['teams'], alliance_selections)
                    for i, complete_alliance in enumerate(complete_alliances):  # search for alliance. could be more efficient
                        if len(set(alliance).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                            backups = list(set(alliance).difference(set(complete_alliance)))
                            complete_alliances[i] += backups  # ensures that backup robots are listed last
                            alliance_names[i] = alliance_name
                            break
                    else:
                        i = None
                        complete_alliances.append(alliance)
                        alliance_names.append(alliance_name)

                    is_new = False
                    if i is not None:
                        for j, (complete_alliance, champ_points, _, match_points, _, _, record) in enumerate(advancement[comp_level]):  # search for alliance. could be more efficient
                            if len(set(complete_alliances[i]).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                                if not match.has_been_played:
                                    cp = 0
                                elif match.winning_alliance == color:
                                    cp = 2
                                    record['wins'] += 1
                                elif match.winning_alliance == '':
                                    cp = 1
                                    record['ties'] += 1
                                else:
                                    cp = 0
                                    record['losses'] += 1
                                if match.has_been_played:
                                    champ_points.append(cp)
                                    match_points.append(match.alliances[color]['score'])
                                    advancement[comp_level][j][2] = sum(champ_points)
                                    advancement[comp_level][j][4] = sum(match_points)
                                break
                        else:
                            is_new = True

                    score = match.alliances[color]['score'] if match.has_been_played else 0
                    record = {'wins': 0, 'losses': 0, 'ties': 0}
                    if not match.has_been_played:
                        cp = 0
                    elif match.winning_alliance == color:
                        cp = 2
                        record['wins'] += 1
                    elif match.winning_alliance == '':
                        cp = 1
                        record['ties'] += 1
                    else:
                        cp = 0
                        record['losses'] += 1
                    if i is None:
                        advancement[comp_level].append([alliance, [cp], cp, [score], score, alliance_name, record])
                    elif is_new:
                        advancement[comp_level].append([complete_alliances[i], [cp], cp, [score], score, alliance_names[i], record])

            advancement[comp_level] = sorted(advancement[comp_level], key=lambda x: -x[4])  # sort by match points
            advancement[comp_level] = sorted(advancement[comp_level], key=lambda x: -x[2])  # sort by championship points
            advancement['{}_complete'.format(comp_level)] = not any_unplayed

        return advancement

    @classmethod
    def getOrderedAlliance(cls, team_keys, alliance_selections):
        if alliance_selections:
            for alliance_selection in alliance_selections:  # search for alliance. could be more efficient
                picks = alliance_selection['picks']
                if len(set(picks).intersection(set(team_keys))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                    backups = list(set(team_keys).difference(set(picks)))
                    team_keys = picks + backups
                    break

        team_nums = []
        for team in team_keys:
            # Strip the "frc" prefix
            team_nums.append(team[3:])
        return team_nums

    @classmethod
    def getAllianceName(cls, team_keys, alliance_selections):
        if alliance_selections:
            for alliance_selection in alliance_selections:  # search for alliance. could be more efficient
                picks = alliance_selection['picks']
                if len(set(picks).intersection(set(team_keys))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                    return alliance_selection.get('name')

        return ''

    """
    Valid breakdowns are those used for seeding. Varies by year.
    For 2014, seeding outlined in Section 5.3.4 in the 2014 manual.
    For 2016+, valid breakdowns match those provided by the FRC API.
    """
    VALID_BREAKDOWNS = {
        2014: set(['auto', 'assist', 'truss+catch', 'teleop_goal+foul']),
        2015: set(['coopertition_points', 'auto_points', 'container_points', 'tote_points', 'litter_points', 'foul_points']),
        2016: set([
            'adjustPoints', 'autoBoulderPoints', 'autoBouldersHigh', 'autoBouldersLow',
            'autoCrossingPoints', 'autoPoints', 'autoReachPoints', 'breachPoints',
            'capturePoints', 'foulCount', 'foulPoints', 'position1crossings',
            'position2', 'position2crossings', 'position3', 'position3crossings',
            'position4', 'position4crossings', 'position5', 'position5crossings',
            'robot1Auto', 'robot2Auto', 'robot3Auto', 'techFoulCount',
            'teleopBoulderPoints', 'teleopBouldersHigh', 'teleopBouldersLow',
            'teleopChallengePoints', 'teleopCrossingPoints', 'teleopDefensesBreached',
            'teleopPoints', 'teleopScalePoints', 'teleopTowerCaptured', 'totalPoints',
            'towerEndStrength', 'towerFaceA', 'towerFaceB', 'towerFaceC'])
    }

    @classmethod
    def is_valid_score_breakdown_key(cls, key, year):
        """
        If valid, returns True. Otherwise, returns the set of valid breakdowns.
        """
        valid_breakdowns = cls.VALID_BREAKDOWNS.get(year, set())
        if key in valid_breakdowns:
            return True
        else:
            return valid_breakdowns

    @classmethod
    def tiebreak_winner(cls, match):
        """
        Compute elim winner using tiebreakers
        """
        if match.comp_level not in match.ELIM_LEVELS or not match.score_breakdown or \
                'red' not in match.score_breakdown or 'blue' not in match.score_breakdown:
            return ''

        red_breakdown = match.score_breakdown['red']
        blue_breakdown = match.score_breakdown['blue']
        tiebreakers = []  # Tuples of (red_tiebreaker, blue_tiebreaker) or None. Higher value wins.
        if match.year == 2016:
            # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
            if 'foulPoints' in red_breakdown and 'foulPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['foulPoints'], blue_breakdown['foulPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative sum of BREACH and CAPTURE points
            if 'breachPoints' in red_breakdown and 'breachPoints' in blue_breakdown and \
                    'capturePoints' in red_breakdown and 'capturePoints' in blue_breakdown:
                red_breach_capture = red_breakdown['breachPoints'] + red_breakdown['capturePoints']
                blue_breach_capture = blue_breakdown['breachPoints'] + blue_breakdown['capturePoints']
                tiebreakers.append((red_breach_capture, blue_breach_capture))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored AUTO points
            if 'autoPoints' in red_breakdown and 'autoPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['autoPoints'], blue_breakdown['autoPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored SCALE and CHALLENGE points
            if 'teleopScalePoints' in red_breakdown and 'teleopScalePoints' in blue_breakdown and \
                    'teleopChallengePoints' in red_breakdown and 'teleopChallengePoints' in blue_breakdown:
                red_scale_challenge = red_breakdown['teleopScalePoints'] + red_breakdown['teleopChallengePoints']
                blue_scale_challenge = blue_breakdown['teleopScalePoints'] + blue_breakdown['teleopChallengePoints']
                tiebreakers.append((red_scale_challenge, blue_scale_challenge))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored TOWER GOAL points (High and Low goals from AUTO and TELEOP)
            if 'autoBoulderPoints' in red_breakdown and 'autoBoulderPoints' in blue_breakdown and \
                    'teleopBoulderPoints' in red_breakdown and 'teleopBoulderPoints' in blue_breakdown:
                red_boulder = red_breakdown['autoBoulderPoints'] + red_breakdown['teleopBoulderPoints']
                blue_boulder = blue_breakdown['autoBoulderPoints'] + blue_breakdown['teleopBoulderPoints']
                tiebreakers.append((red_boulder, blue_boulder))
            else:
                tiebreakers.append(None)

            # Cumulative sum of CROSSED UNDAMAGED DEFENSE points (AUTO and TELEOP)
            if 'autoCrossingPoints' in red_breakdown and 'autoCrossingPoints' in blue_breakdown and \
                    'teleopCrossingPoints' in red_breakdown and 'teleopCrossingPoints' in blue_breakdown:
                red_crossing = red_breakdown['autoCrossingPoints'] + red_breakdown['teleopCrossingPoints']
                blue_crossing = blue_breakdown['autoCrossingPoints'] + blue_breakdown['teleopCrossingPoints']
                tiebreakers.append((red_crossing, blue_crossing))
            else:
                tiebreakers.append(None)
        elif match.year == 2017 and not (match.comp_level == 'f' and match.match_number <= 3):  # Finals can't be tiebroken. Only overtime
            # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
            if 'foulPoints' in red_breakdown and 'foulPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['foulPoints'], blue_breakdown['foulPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored AUTO points
            if 'autoPoints' in red_breakdown and 'autoPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['autoPoints'], blue_breakdown['autoPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative ROTOR engagement score (AUTO and TELEOP)
            if 'autoRotorPoints' in red_breakdown and 'autoRotorPoints' in blue_breakdown and \
                    'teleopRotorPoints' in red_breakdown and 'teleopRotorPoints' in blue_breakdown:
                red_rotor = red_breakdown['autoRotorPoints'] + red_breakdown['teleopRotorPoints']
                blue_rotor = blue_breakdown['autoRotorPoints'] + blue_breakdown['teleopRotorPoints']
                tiebreakers.append((red_rotor, blue_rotor))
            else:
                tiebreakers.append(None)

            # Cumulative TOUCHPAD score
            if 'teleopTakeoffPoints' in red_breakdown and 'teleopTakeoffPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['teleopTakeoffPoints'], blue_breakdown['teleopTakeoffPoints']))
            else:
                tiebreakers.append(None)

            # Total accumulated pressure
            if 'autoFuelPoints' in red_breakdown and 'autoFuelPoints' in blue_breakdown and \
                    'teleopFuelPoints' in red_breakdown and 'teleopFuelPoints' in blue_breakdown:
                red_pressure = red_breakdown['autoFuelPoints'] + red_breakdown['teleopFuelPoints']
                blue_pressure = blue_breakdown['autoFuelPoints'] + blue_breakdown['teleopFuelPoints']
                tiebreakers.append((red_pressure, blue_pressure))
            else:
                tiebreakers.append(None)

        for tiebreaker in tiebreakers:
            if tiebreaker is None:
                return ''
            elif tiebreaker[0] > tiebreaker[1]:
                return 'red'
            elif tiebreaker[1] > tiebreaker[0]:
                return 'blue'
        return ''
