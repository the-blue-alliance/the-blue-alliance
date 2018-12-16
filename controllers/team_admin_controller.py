import logging
import tba_config
from collections import defaultdict

from base_controller import CacheableHandler, LoggedInHandler
from google.appengine.ext import ndb
from helpers.media_manipulator import MediaManipulator
from models.media import Media
from models.suggestion import Suggestion
from models.team import Team
from models.team_admin_access import TeamAdminAccess
from template_engine import jinja2_engine


class TeamAdminDashboard(LoggedInHandler):
    ALLOWED_SUGGESTION_TYPES = ["media", "social-media", "robot"]

    def get(self):
        self._require_registration()
        user = self.user_bundle.account.key

        existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == user).fetch()
        team_keys = [
            ndb.Key(Team, "frc{}".format(access.team_number))
            for access in existing_access
        ]
        teams_future = ndb.get_multi_async(team_keys)
        team_medias_future = Media.query(
            Media.references.IN(team_keys)).fetch_async(50)
        suggestions_future = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
                Suggestion.target_model.IN(self.ALLOWED_SUGGESTION_TYPES),
                Suggestion.target_key.IN(
                    [k.id() for k in team_keys])).fetch_async(limit=50)

        team_num_to_team = {
            team.get_result().team_number: team.get_result()
            for team in teams_future
        }
        team_medias = defaultdict(list)
        for media in team_medias_future.get_result():
            for reference in media.references:
                if reference in team_keys:
                    team_num = reference.id()[3:]
                    team_medias[int(team_num)].append(media)

        suggestions_by_team = defaultdict(list)
        for suggestion in suggestions_future.get_result():
            # Assume all the keys are team keys
            team_num = suggestion.target_key[3:]
            suggestions_by_team[int(team_num)].append(suggestion)

        self.template_values.update({
            "existing_access": existing_access,
            "teams": team_num_to_team,
            "team_medias": team_medias,
            "suggestions_by_team": suggestions_by_team,
        })

        self.response.out.write(
            jinja2_engine.render('team_admin_dashboard.html',
                                 self.template_values))

    def post(self):
        team_number = self.request.get("team_number")
        if not team_number:
            self.abort(400)
        team_number = int(team_number)
        self._require_team_admin_access(team_number)

        media_key_name = self.request.get("media_key_name")
        media = Media.get_by_id(media_key_name)
        if not media:
            self.abort(400)
        team_ref = Media.create_reference('team', 'frc{}'.format(team_number))
        action = self.request.get('action')
        if action == "remove_media_reference":
            if team_ref in media.references:
                media.references.remove(team_ref)
            if team_ref in media.preferred_references:
                media.preferred_references.remove(team_ref)
        elif action == "remove_media_preferred":
            if team_ref in media.preferred_references:
                media.preferred_references.remove(team_ref)
        elif action == "add_media_preferred":
            if team_ref not in media.preferred_references:
                media.preferred_references.append(team_ref)
        else:
            self.abort(400)

        MediaManipulator.createOrUpdate(media, auto_union=False)
        self.redirect('/mod/')


class TeamAdminRedeem(LoggedInHandler):
    def get(self):
        self._require_registration()
        user = self.user_bundle.account.key

        existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == user).fetch()

        team_keys = [
            ndb.Key(Team, "frc{}".format(access.team_number))
            for access in existing_access
        ]
        teams = ndb.get_multi(team_keys)
        team_num_to_team = {team.team_number: team for team in teams}

        self.template_values.update({
            "existing_access": existing_access,
            "status": self.request.get("status"),
            "team": self.request.get("team"),
            "teams": team_num_to_team,
        })

        self.response.out.write(
            jinja2_engine.render('team_admin_redeem.html',
                                 self.template_values))

    def post(self):
        self._require_registration()
        user = self.user_bundle.account.key

        auth_code = self.request.get("auth_code")
        access = TeamAdminAccess.query(
            TeamAdminAccess.access_code == auth_code).fetch()
        existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == user).fetch()
        if existing_access:
            self.redirect('/mod/redeem?status=already_linked')
            return
        if not access:
            self.redirect('/mod/redeem?status=invalid_code')
            return

        access = access[0]
        if access.account:
            self.redirect('/mod/redeem?status=code_used')
            return
        access.account = user
        access.put()

        self.redirect('/mod/redeem?status=success&team={}'.format(
            access.team_number))


class ModHelpHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "mod_help"

    def __init__(self, *args, **kw):
        super(ModHelpHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('modhelp.html', self.template_values)
