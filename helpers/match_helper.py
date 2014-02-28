import logging
import datetime
import pytz
import re

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
        def cmp_matches(x, y):
            if x.updated is None:
                return False
            if y.updated is None:
                return True
            else:
                cmp(x.updated, y.updated)

        matches = filter(lambda x: x.has_been_played, matches)
        matches = MatchHelper.organizeMatches(matches)

        all_matches = []
        for comp_level in Match.COMP_LEVELS:
            if comp_level in matches:
                play_order_sorted = self.play_order_sort_matches(matches[comp_level])
                all_matches += play_order_sorted
        return all_matches[-num:]

    @classmethod
    def upcomingMatches(self, matches, num=3):
        matches = filter(lambda x: not x.has_been_played, matches)
        matches = MatchHelper.organizeMatches(matches)

        unplayed_matches = []
        for comp_level in Match.COMP_LEVELS:
            if comp_level in matches:
                play_order_sorted = self.play_order_sort_matches(matches[comp_level])
                for match in play_order_sorted:
                    unplayed_matches.append(match)
        return unplayed_matches[:num]

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
                if match_1 != None and match_2 != None and\
                    match_1.has_been_played and match_2.has_been_played and\
                    match_1.winning_alliance == match_2.winning_alliance:
                        try:
                            match.key.delete()
                            logging.warning("Deleting invalid match: %s" % match.key_name)
                        except:
                            logging.warning("Tried to delete invalid match, but failed: %s" % match.key_name)
                        continue
            return_list.append(match)
        return return_list

    @classmethod
    def generateBracket(self, matches):
        results = {}
        for match in matches:
            set_number = str(match.set_number)

            if set_number not in results:
                red_alliance = []
                for team in match.alliances['red']['teams']:
                    red_alliance.append(team[3:])
                blue_alliance = []
                for team in match.alliances['blue']['teams']:
                    blue_alliance.append(team[3:])

                results[set_number] = {'red_alliance': red_alliance,
                                       'blue_alliance': blue_alliance,
                                       'winning_alliance': None,
                                       'red_wins': 0,
                                       'blue_wins': 0}
            winner = match.winning_alliance
            if not winner or winner == '':
                # if the match is a tie
                continue

            results[set_number]['{}_wins'.format(winner)] = \
                results[set_number]['{}_wins'.format(winner)] + 1
            if results[set_number]['red_wins'] == 2:
                results[set_number]['winning_alliance'] = 'red'
            if results[set_number]['blue_wins'] == 2:
                results[set_number]['winning_alliance'] = 'blue'

        return results
