import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler

from helpers.media_helper import MediaHelper, MediaParser
from helpers.suggestions.suggestion_creator import SuggestionCreator

from models.media import Media
from models.team import Team

from template_engine import jinja2_engine


class SuggestTeamMediaController(LoggedInHandler):
    """
    Allow users to suggest media for TBA to add to teams.
    """

    def get(self):
        team_key = self.request.get("team_key")
        year_str = self.request.get("year")

        self._require_login("/suggest/team/media?team_key=%s&year=%s" % (team_key, year_str))

        if not team_key or not year_str:
            self.redirect("/", abort=True)

        year = int(year_str)
        team_future = Team.get_by_id_async(self.request.get("team_key"))
        team = team_future.get_result()
        media_key_futures = Media.query(Media.references == team.key, Media.year == year).fetch_async(500, keys_only=True)
        media_futures = ndb.get_multi_async(media_key_futures.get_result())
        medias_by_slugname = MediaHelper.group_by_slugname([media_future.get_result() for media_future in media_futures])

        self.template_values.update({
            "status": self.request.get("status"),
            "team": team,
            "year": year,
            "medias_by_slugname": medias_by_slugname
        })

        self.response.out.write(jinja2_engine.render('suggest_team_media.html', self.template_values))

    def post(self):
        self._require_login()

        team_key = self.request.get("team_key")
        year_str = self.request.get("year")

        status = SuggestionCreator.createTeamMediaSuggestion(
            author_account_key=self.user_bundle.account.key,
            media_url=self.request.get("media_url"),
            team_key=team_key,
            year_str=year_str)

        self.redirect('/suggest/team/media?team_key=%s&year=%s&status=%s' % (team_key, year_str, status))
