import json

from api.apiv3.api_base_controller import ApiBaseController
from database.team_query import TeamParticipationQuery
from helpers.suggestions.suggestion_creator import SuggestionCreator


class ApiSuggestTeamMediaController(ApiBaseController):
    CACHE_VERSION = 0

    def _track_call(self, team_key, year):
        self._track_call_defer('team/suggest/media', team_key)

    def _render(self, team_key, year):
        if int(year) not in list(TeamParticipationQuery(team_key).fetch()):
            self.abort(404)

        if 'media_url' in self.request.POST:
            status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
                author_account_key=self.auth_owner_key,
                media_url=self.request.POST["media_url"],
                team_key=team_key,
                year_str=year)

            if status == 'success':
                message = {
                    "success": True
                }
            else:
                message = {
                    "success": False,
                    "message": status
                }
        else:
            message = {
                "success": False,
                "message": "missing media_url"
            }

        return json.dumps(message, ensure_ascii=True, indent=2, sort_keys=True)
