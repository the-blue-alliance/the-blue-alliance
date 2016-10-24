import logging
import copy
import datetime
import pytz
import re

from collections import defaultdict

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
    def deleteInvalidMatches(self, match_list):
        """
        A match is invalid iff it is an elim match where the match number is 3
        and the same alliance won in match numbers 1 and 2 of the same set.
        """
        matches_by_key = {}
        for match in match_list:
            matches_by_key[match.key_name] = match

        return_list = []
        for match in match_list:
            if match.comp_level in Match.ELIM_LEVELS and match.match_number == 3 and (not match.has_been_played):
                match_1 = matches_by_key.get(Match.renderKeyName(match.event.id(), match.comp_level, match.set_number, 1))
                match_2 = matches_by_key.get(Match.renderKeyName(match.event.id(), match.comp_level, match.set_number, 2))
                if match_1 is not None and match_2 is not None and\
                    match_1.has_been_played and match_2.has_been_played and\
                    match_1.winning_alliance == match_2.winning_alliance:
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

        for tiebreaker in tiebreakers:
            if tiebreaker is None:
                return ''
            elif tiebreaker[0] > tiebreaker[1]:
                return 'red'
            elif tiebreaker[1] > tiebreaker[0]:
                return 'blue'
        return ''
