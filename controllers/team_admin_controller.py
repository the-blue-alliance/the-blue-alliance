import tba_config

from base_controller import CacheableHandler, LoggedInHandler
from google.appengine.ext import ndb
from models.team import Team
from models.team_admin_access import TeamAdminAccess
from template_engine import jinja2_engine


class TeamAdminDashboard(LoggedInHandler):
    def get(self):
        self._require_registration()

        self.response.out.write(
            jinja2_engine.render('team_admin_dashboard.html',
                                 self.template_values))


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
