import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from helpers.social_connection_helper import SocialConnectionHelper
from models.social_connection import SocialConnection
from models.suggestion import Suggestion
from models.team import Team


class SuggestTeamSocialController(LoggedInHandler):
    """
    Allow users to suggest social network accounts for TBA to add to teams.
    """

    def get(self):
        team_key = self.request.get("team_key")

        self._require_login("/suggest/team/social?team_key=%s" % (team_key))

        if not team_key:
            self.redirect("/", abort=True)

        team_future = Team.get_by_id_async(self.request.get("team_key"))
        team = team_future.get_result()
        social_key_futures = SocialConnection.query(SocialConnection.parent_model == team.key).fetch_async(500, keys_only=True)
        social_futures = ndb.get_multi_async(social_key_futures.get_result())
        connections_by_type = SocialConnectionHelper.group_by_type([social_future.get_result() for social_future in social_futures])

        self.template_values.update({
            "success": self.request.get("success"),
            "team": team,
            "connections_by_type": connections_by_type
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_social_connection.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login()

        team_key = self.request.get("team_key")
        year_str = self.request.get("year")

        success_code = 0
        media_dict = MediaParser.partial_media_dict_from_url(self.request.get('media_url').strip())
        if media_dict is not None:
            existing_media = Media.get_by_id(Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']))
            if existing_media is None or team_key not in [reference.id() for reference in existing_media.references]:
                media_dict['year'] = int(year_str)
                media_dict['reference_type'] = 'team'
                media_dict['reference_key'] = team_key

                suggestion = Suggestion(
                    author=self.user_bundle.account.key,
                    target_model="media",
                    )
                suggestion.contents = media_dict
                suggestion.put()
            success_code = 1

        self.redirect('/suggest/team/media?team_key=%s&year=%s&success=%s' % (team_key, year_str, success_code))
