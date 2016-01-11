import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from helpers.social_connection_helper import SocialConnectionHelper, SocialConnectionParser
from models.social_connection import SocialConnection
from models.suggestion import Suggestion
from models.team import Team


class SuggestSocialProfileController(LoggedInHandler):
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
        social_key_futures = SocialConnection.query(SocialConnection.references == team.key).fetch_async(500, keys_only=True)
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
        social_url = self.request.get("social_url").strip()

        success_code = 0
        social_dict = SocialConnectionParser.partial_social_dict_from_url(social_url)
        if social_dict is not None:
            existing_key = SocialConnection.render_key_name(social_dict['social_type_enum'], social_dict['foreign_key'])
            existing_connection = SocialConnection.get_by_id(existing_key)
            if existing_connection is None or team_key not in [reference.id() for reference in existing_connection.references]:
                social_dict['reference_type'] = 'team'
                social_dict['reference_key'] = team_key

                suggestion = Suggestion(
                    author=self.user_bundle.account.key,
                    target_model="social_connection",
                    )
                suggestion.contents = social_dict
                suggestion.put()
            success_code = 1

        self.redirect('/suggest/team/social?team_key=%s&success=%s' % (team_key, success_code))
