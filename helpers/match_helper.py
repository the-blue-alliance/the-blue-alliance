import logging
from collections import defaultdict
import copy
import datetime
import json
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
        import pytz
        if event.timezone_id is None:  # Can only calculate match times if event timezone is known
            logging.warning('Cannot compute match time for event with no timezone_id: {}'.format(event.key_name))
            return

        matches_reversed = cls.play_order_sort_matches(matches, reverse=True)
        tz = pytz.timezone(event.timezone_id)

        last_match_time = None
        cur_date = event.end_date + datetime.timedelta(hours=23, minutes=59, seconds=59)  # end_date is specified at midnight of the last day
        for match in matches_reversed:
            r = re.search(r'(\d+):(\d+) (am|pm)', match.time_string.lower())
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

    # Assumed that organizeMatches is called first
    @classmethod
    def organizeDoubleElimMatches(cls, organized_matches):
        matches = defaultdict(lambda: defaultdict(list))
        for level in Match.COMP_LEVELS:
            level_matches = organized_matches[level]
            if level == 'qm':
                matches['qm'] = level_matches
                continue
            for match in level_matches:
                bracket = PlayoffType.get_double_elim_bracket(level, match.set_number)
                matches[bracket][level].append(match)
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
                    n = 3 if event.playoff_type == PlayoffType.BO5_FINALS else 2
                    if red_win_counts[key] == n or blue_win_counts[key] == n:
                        try:
                            MatchManipulator.delete(match)
                            logging.warning("Deleting invalid match: %s" % match.key_name)
                        except:
                            logging.warning("Tried to delete invalid match, but failed: %s" % match.key_name)
                        continue
            return_list.append(match)

        return return_list

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
            'towerEndStrength', 'towerFaceA', 'towerFaceB', 'towerFaceC']),
        2017: set([
            'adjustPoints', 'autoFuelHigh', 'autoFuelLow', 'autoFuelPoints',
            'autoMobilityPoints', 'autoPoints', 'autoRotorPoints', 'foulCount', 'foulPoints',
            'kPaBonusPoints', 'kPaRankingPointAchieved', 'robot1Auto', 'robot2Auto', 'robot3Auto',
            'rotor1Auto', 'rotor1Engaged', 'rotor2Auto', 'rotor2Engaged', 'rotor3Engaged', 'rotor4Engaged',
            'rotorBonusPoints', 'rotorRankingPointAchieved', 'techFoulCount', 'teleopFuelHigh',
            'teleopFuelLow', 'teleopFuelPoints', 'teleopPoints', 'teleopRotorPoints', 'teleopTakeoffPoints',
            'totalPoints', 'touchpadFar', 'touchpadMiddle', 'touchpadNear']),
        2018: set([
            'autoRobot1', 'autoRobot2', 'autoRobot3', 'autoSwitchOwnershipSec', 'autoScaleOwnershipSec',
            'autoSwitchAtZero', 'autoRunPoints', 'autoOwnershipPoints', 'autoPoints',
            'teleopSwitchOwnershipSec', 'teleopScaleOwnershipSec', 'teleopSwitchBoostSec',
            'teleopScaleBoostSec', 'teleopSwitchForceSec', 'teleopScaleForceSec',
            'vaultForceTotal', 'vaultForcePlayed', 'vaultLevitateTotal', 'vaultLevitatePlayed',
            'vaultBoostTotal', 'vaultBoostPlayed', 'endgameRobot1', 'endgameRobot2', 'endgameRobot3',
            'teleopOwnershipPoints', 'vaultPoints', 'endgamePoints', 'teleopPoints',
            'autoQuestRankingPoint', 'faceTheBossRankingPoint', 'foulCount', 'techFoulCount',
            'adjustPoints', 'foulPoints', 'rp', 'totalPoints', 'tba_gameData']),
        2019: set([
            'adjustPoints', 'autoPoints', 'bay1', 'bay2', 'bay3', 'bay4',
            'bay5', 'bay6', 'bay7', 'bay8', 'cargoPoints',
            'completeRocketRankingPoint', 'completedRocketFar',
            'completedRocketNear', 'endgameRobot1', 'endgameRobot2',
            'endgameRobot3', 'foulCount', 'foulPoints', 'habClimbPoints',
            'habDockingRankingPoint', 'habLineRobot1', 'habLineRobot2',
            'habLineRobot3', 'hatchPanelPoints', 'lowLeftRocketFar',
            'lowLeftRocketNear', 'lowRightRocketFar', 'lowRightRocketNear',
            'midLeftRocketFar', 'midLeftRocketNear', 'midRightRocketFar',
            'midRightRocketNear', 'preMatchBay1', 'preMatchBay2',
            'preMatchBay3', 'preMatchBay6', 'preMatchBay7', 'preMatchBay8',
            'preMatchLevelRobot1', 'preMatchLevelRobot2', 'preMatchLevelRobot3',
            'rp', 'sandStormBonusPoints', 'techFoulCount', 'teleopPoints',
            'topLeftRocketFar', 'topLeftRocketNear', 'topRightRocketFar',
            'topRightRocketNear', 'totalPoints']),
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
        elif match.year == 2019 and not (match.comp_level == 'f' and match.match_number <= 3):  # Finals can't be tiebroken. Only overtime
            # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
            if 'foulPoints' in red_breakdown and 'foulPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['foulPoints'], blue_breakdown['foulPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored CARGO points
            if 'cargoPoints' in red_breakdown and 'cargoPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['cargoPoints'], blue_breakdown['cargoPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored HATCH PANEL points
            if 'hatchPanelPoints' in red_breakdown and 'hatchPanelPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['hatchPanelPoints'], blue_breakdown['hatchPanelPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored HAB CLIMB points
            if 'habClimbPoints' in red_breakdown and 'habClimbPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['habClimbPoints'], blue_breakdown['habClimbPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative sum of scored SANDSTORM BONUS points
            if 'sandStormBonusPoints' in red_breakdown and 'sandStormBonusPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['sandStormBonusPoints'], blue_breakdown['sandStormBonusPoints']))
            else:
                tiebreakers.append(None)
        elif match.year == 2020 and not (match.comp_level == 'f' and match.match_number <= 3):  # Finals can't be tiebroken. Only overtime
            # Cumulative FOUL and TECH FOUL points due to opponent rule violations
            if 'foulPoints' in red_breakdown and 'foulPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['foulPoints'], blue_breakdown['foulPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative AUTO points
            if 'autoPoints' in red_breakdown and 'autoPoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['autoPoints'], blue_breakdown['autoPoints']))
            else:
                tiebreakers.append(None)

            # Cumulative ENDGAME points
            if 'endgamePoints' in red_breakdown and 'endgamePoints' in blue_breakdown:
                tiebreakers.append((red_breakdown['endgamePoints'], blue_breakdown['endgamePoints']))
            else:
                tiebreakers.append(None)

            # Cumulative TELEOP POWER CELL and CONTROL PANEL points
            if 'teleopCellPoints' in red_breakdown and 'teleopCellPoints' in blue_breakdown and \
                    'controlPanelPoints' in red_breakdown and 'controlPanelPoints' in blue_breakdown:
                tiebreakers.append((
                    red_breakdown['teleopCellPoints'] + red_breakdown['controlPanelPoints'],
                    blue_breakdown['teleopCellPoints'] + blue_breakdown['controlPanelPoints'],
                ))
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
