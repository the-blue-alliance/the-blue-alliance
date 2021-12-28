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
    def add_surrogates(cls, event):
        """
        If a team has more scheduled matches than other teams, then the third
        match is a surrogate.
        Valid for 2008 and up, don't compute for offseasons.
        """
        if event.year < 2008 or event.event_type_enum not in EventType.SEASON_EVENT_TYPES:
            return

        qual_matches = cls.organized_matches(event.matches)['qm']
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
    def delete_invalid_matches(self, match_list, event):
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
