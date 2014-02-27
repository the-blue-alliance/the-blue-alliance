import logging

from models.match import Match


class MatchHelper(object):
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
