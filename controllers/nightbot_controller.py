from base_controller import CacheableHandler
from database.event_query import TeamEventsQuery
from database.match_query import TeamEventMatchesQuery
from helpers.match_helper import MatchHelper
from models.team import Team


def validate_team(user_str, team_number):
    """
    Returns:
    Team object if the team exists and is currently competing
    String with the appropriate error otherwise
    """
    team_key = 'frc{}'.format(team_number)
    team = Team.get_by_id(team_key)
    if not team:
        return "{}Team {} does not exist.".format(user_str, team_number)

    team_events_future = TeamEventsQuery(team_key).fetch_async()
    current_event = None
    for event in team_events_future.get_result():
        if event.now:
            current_event = event
    if not current_event:
        return "{}Team {} is not currently competing.".format(user_str, team_number)

    return team, current_event


class NightbotTeamNextmatchHandler(CacheableHandler):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "nightbot_team_nextmatch_{}"  # (team_number)
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(NightbotTeamNextmatchHandler, self).__init__(*args, **kw)
        self._cache_expiration = self.CACHE_HEADER_LENGTH

    def get(self, team_number):
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(team_number)
        super(NightbotTeamNextmatchHandler, self).get(team_number)

    def _render(self, team_number):
        self.response.headers['content-type'] = 'text/plain; charset="utf-8"'
        user = self.request.get('user')
        if user:
            user_str = '{}, '.format(user)
        else:
            user_str = ''

        team_event_or_error = validate_team(user_str, team_number)
        if type(team_event_or_error) == str:
            return team_event_or_error

        _, event = team_event_or_error

        matches_future = TeamEventMatchesQuery('frc{}'.format(team_number), event.key.id()).fetch_async()
        matches = MatchHelper.play_order_sort_matches(matches_future.get_result())
        next_match = None
        for match in matches:
            if not match.has_been_played:
                next_match = match
                break

        event_code_upper = event.event_short.upper()
        if next_match is None:
            return "{}[{}] Team {} has no more scheduled matches.".format(user_str, event_code_upper, team_number)

        return "{}[{}] Team {} will be playing in match {}.".format(user_str, event_code_upper, team_number, match.short_name)


class NightbotTeamStatuskHandler(CacheableHandler):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "nightbot_team_status_{}"  # (team_number)
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(NightbotTeamStatuskHandler, self).__init__(*args, **kw)
        self._cache_expiration = self.CACHE_HEADER_LENGTH

    def get(self, team_number):
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(team_number)
        super(NightbotTeamStatuskHandler, self).get(team_number)

    def _render(self, team_number):
        self.response.headers['content-type'] = 'text/plain; charset="utf-8"'
        user = self.request.get('user')
        if user:
            user_str = '{}, '.format(user)
        else:
            user_str = ''

        team_event_or_error = validate_team(user_str, team_number)
        if type(team_event_or_error) == str:
            return team_event_or_error

        _, event = team_event_or_error
        event_code_upper = event.event_short.upper()

        team_key = 'frc{}'.format(team_number)
        matches_future = TeamEventMatchesQuery(team_key, event.key.id()).fetch_async()
        matches = MatchHelper.organizeMatches(matches_future.get_result())

        # Compute alliances
        alliance_number = None
        if event.alliance_selections:
            for i, alliance in enumerate(event.alliance_selections):
                if team_key in alliance['picks']:
                    alliance_number = i + 1
                    break
            else:
                alliance_number = 0  # Team didn't make it to elims

        level_map = {
            'qf': 'quarters',
            'sf': 'semis',
            'f': 'the finals',
        }
        for comp_level in ['f', 'sf', 'qf']:  # playoffs
            level_str = level_map[comp_level]
            if matches[comp_level]:
                wins = 0
                losses = 0
                for match in matches[comp_level]:
                    if match.has_been_played:
                        if team_key in match.alliances[match.winning_alliance]['teams']:
                            wins += 1
                        else:
                            losses += 1
                if wins == 2:
                    if comp_level == 'f':
                        return "{}[{}] Team {} won the event on alliance #{}.".format(user_str, event_code_upper, team_number, alliance_number)
                    else:
                        return "{}[{}] Team {} won {} on alliance #{}.".format(user_str, event_code_upper, team_number, level_str, alliance_number)
                elif losses == 2:
                    return "{}[{}] Team {} got knocked out in {} on alliance #{}.".format(user_str, event_code_upper, team_number, level_str, alliance_number)
                else:
                    return "{}[{}] Team {} is currently {}-{} in {} on alliance #{}.".format(user_str, event_code_upper, team_number, wins, losses, level_str, alliance_number)

        # Still in quals or team did not make it to elims
        # Compute qual W-L-T
        wins = 0
        losses = 0
        ties = 0
        unplayed_qual = 0
        for match in matches['qm']:
            if match.has_been_played:
                if match.winning_alliance == '':
                    ties += 1
                elif team_key in match.alliances[match.winning_alliance]['teams']:
                    wins += 1
                else:
                    losses += 1
            else:
                unplayed_qual += 1

        # Compute rank & num_teams
        rank = None
        if event.rankings:
            num_teams = len(event.rankings) - 1
            for i, row in enumerate(event.rankings):
                if row[1] == team_number:
                    rank = i

        if unplayed_qual > 0:
            if rank is not None:
                return "{}[{}] Team {} is currently rank {}/{} with a record of {}-{}-{}.".format(user_str, event_code_upper, team_number, rank, num_teams, wins, losses, ties)
            else:
                return "{}[{}] Team {} currently has a record of {}-{}-{} at [{}].".format(user_str, event_code_upper, team_number, wins, losses, ties)
        else:
            if alliance_number is None:
                return "{}[{}] Team {} ended qualification matches at rank {}/{} with a record of {}-{}-{}.".format(user_str, event_code_upper, team_number, rank, num_teams, wins, losses, ties)
            elif alliance_number == 0:
                return "{}[{}] Team {} ended qualification matches at rank {}/{} with a record of {}-{}-{} and was not picked for playoff matches.".format(user_str, event_code_upper, team_number, rank, num_teams, wins, losses, ties)
            else:
                return "{}[{}] Team {} will be competing in the playoff matches on alliance #{}.".format(user_str, event_code_upper, team_number, alliance_number)
