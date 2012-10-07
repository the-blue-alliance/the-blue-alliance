import logging

from models.match import Match
from models.team import Team

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
        alphanum_key = lambda match: [ convert(c) for c in re.split('([0-9]+)', str(match.key_name)) ] 
        return sorted(matches, key = alphanum_key)

    @classmethod
    def organizeMatches(self, match_list):
        match_list = match_list.fetch(500)
        match_list = MatchHelper.natural_sort_matches(match_list)

        # Cleanup invalid. This does database calls. This is a wildly inappropriate place
        # to be doing this. -gregmarra
        match_list = filter(None, [MatchHelper.cleanUpIfInvalidMatch(match) for match in match_list])
        
        matches = dict([(comp_level, list()) for comp_level in Match.COMP_LEVELS])
        matches["num"] = len(match_list)
        while len(match_list) > 0:
            match = match_list.pop(0)
            matches[match.comp_level].append(match)
        
        return matches
    
    @classmethod
    def cleanUpIfInvalidMatch(self, match):
        invalid = MatchHelper.isIncompleteElim(match)
        if invalid:
            match.delete()
            logging.warning("Deleting invalid match: %s" % match.key_name)
            return None
        else:
            return match
    
    @classmethod
    def isIncompleteElim(self, match):
        if match.comp_level not in set(["ef", "qf", "sf", "f"]):
            return False
        
        for alliance in match.alliances:
            if match.alliances[alliance]["score"] > -1:
                return False
        
        # No alliances had non-zero scores
        return True
    
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
