import json
import logging
import os

from google.appengine.ext import ndb

from consts.media_type import MediaType
from controllers.base_controller import LoggedInHandler

from database import media_query

from helpers.media_helper import MediaHelper, MediaParser
from helpers.suggestions.suggestion_creator import SuggestionCreator
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from models.media import Media
from models.sitevar import Sitevar
from models.team import Team

from template_engine import jinja2_engine


class SuggestTeamMediaController(LoggedInHandler):
    """
    Allow users to suggest media for TBA to add to teams.
    """

    def get(self):
        team_key = self.request.get("team_key")
        year_str = self.request.get("year")

        self._require_registration()

        if not team_key or not year_str:
            self.redirect("/", abort=True)

        year = int(year_str)
        team_future = Team.get_by_id_async(self.request.get("team_key"))
        team = team_future.get_result()
        if not team:
            self.redirect("/", abort=True)

        media_key_futures = Media.query(Media.references == team.key, Media.year == year).fetch_async(500, keys_only=True)
        social_media_future = media_query.TeamSocialMediaQuery(team.key.id()).fetch_async()

        media_futures = ndb.get_multi_async(media_key_futures.get_result())
        medias = [media_future.get_result() for media_future in media_futures]
        medias_by_slugname = MediaHelper.group_by_slugname(medias)

        social_medias = sorted(social_media_future.get_result(), key=MediaHelper.social_media_sorter)
        social_medias = filter(lambda m: m.media_type_enum == MediaType.INSTAGRAM_PROFILE, social_medias)  # we only allow IG media, so only show IG profile

        self.template_values.update({
            "medias_by_slugname": medias_by_slugname,
            "social_medias": social_medias,
            "status": self.request.get("status"),
            "team": team,
            "year": year,
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_team_media.html', self.template_values))

    def post(self):
        self._require_registration()

        team_key = self.request.get("team_key")
        year_str = self.request.get("year")

        status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
            author_account_key=self.user_bundle.account.key,
            media_url=self.request.get("media_url"),
            team_key=team_key,
            year_str=year_str)

        if status == 'success' and suggestion.contents.get('media_type') == MediaType.GRABCAD:
            # Send an update to the frcdesigns slack
            slack_sitevar = Sitevar.get_or_insert('slack.hookurls')
            if slack_sitevar:
                slack_url = slack_sitevar.contents.get('tbablog', '')
                if slack_url:
                    model_details = json.loads(suggestion.contents['details_json'])
                    message_body = u"{0} ({1}) has suggested a CAD model for team <https://www.thebluealliance.com/team/{2}/{3}|{2} in {3}>.".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        team_key[3:],
                        year_str).encode('utf-8')
                    image_attachment = {
                        "footer": "<https://www.thebluealliance.com/suggest/cad/review|See all suggestions> on The Blue Alliance",
                        "fallback": "CAD model",
                        "title": model_details['model_name'],
                        "title_link": "https://grabcad.com/library/{}".format(suggestion.contents['foreign_key']),
                        "image_url": model_details['model_image'].replace('card.jpg', 'large.png'),
                        "fields": [
                            {
                                "title": "Accept",
                                "value": "<https://www.thebluealliance.com/suggest/cad/review?action=accept&id={}|Click Here>".format(suggestion.key.id()),
                                "short": True,
                            },
                            {
                                "title": "Reject",
                                "value": "<https://www.thebluealliance.com/suggest/cad/review?action=reject&id={}|Click Here>".format(suggestion.key.id()),
                                "short": True,
                            }
                        ],
                    }

                    OutgoingNotificationHelper.send_slack_alert(slack_url, message_body, [image_attachment])

        self.redirect('/suggest/team/media?team_key=%s&year=%s&status=%s' % (team_key, year_str, status))


class SuggestTeamSocialMediaController(LoggedInHandler):
    """
    Allow users to suggest social media for TBA to add to teams.
    """

    def get(self):
        team_key = self.request.get("team_key")

        self._require_registration()

        if not team_key:
            self.redirect("/", abort=True)

        team_future = Team.get_by_id_async(self.request.get("team_key"))
        team = team_future.get_result()
        if not team:
            self.redirect("/", abort=True)

        media_key_futures = Media.query(Media.references == team.key, Media.year == None).fetch_async(500, keys_only=True)
        media_futures = ndb.get_multi_async(media_key_futures.get_result())
        medias = [media_future.get_result() for media_future in media_futures]
        social_medias = MediaHelper.get_socials(medias)

        self.template_values.update({
            "status": self.request.get("status"),
            "team": team,
            "social_medias": social_medias,
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_team_social_media.html', self.template_values))

    def post(self):
        self._require_registration()

        team_key = self.request.get("team_key")

        status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
            author_account_key=self.user_bundle.account.key,
            media_url=self.request.get("media_url"),
            team_key=team_key,
            year_str=None,
            is_social=True)

        self.redirect('/suggest/team/social_media?team_key=%s&status=%s' % (team_key, status))
