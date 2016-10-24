from base_controller import CacheableHandler
from database.event_query import TeamEventsQuery
from database.match_query import TeamEventMatchesQuery
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.match_helper import MatchHelper
from helpers.team_helper import TeamHelper
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
            user_str = '@{}, '.format(user)
        else:
            user_str = ''

        team_event_or_error = validate_team(user_str, team_number)
        if type(team_event_or_error) == str:
            return team_event_or_error

        _, event = team_event_or_error
        event_code_upper = event.event_short.upper()

        matches_future = TeamEventMatchesQuery('frc{}'.format(team_number), event.key.id()).fetch_async()
        matches = MatchHelper.play_order_sort_matches(matches_future.get_result())

        # No match schedule yet
        if not matches:
            return "{}[{}] Team {} has no scheduled matches yet.".format(user_str, event_code_upper, team_number)

        next_match = None
        for match in matches:
            if not match.has_been_played:
                next_match = match
                break

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
            user_str = '@{}, '.format(user)
        else:
            user_str = ''

        team_event_or_error = validate_team(user_str, team_number)
        if type(team_event_or_error) == str:
            return team_event_or_error

        _, event = team_event_or_error
        event_code_upper = event.event_short.upper()

        team_key = 'frc{}'.format(team_number)
        status = EventTeamStatusHelper.generateTeamAtEventStatusAsync(team_key, event).get_result()[0]
        return '{}[{}] {}'.format(user_str, event_code_upper, status)
