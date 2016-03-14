import json
import logging
import random
import string
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.auth_type import AuthType
from controllers.base_controller import LoggedInHandler

from models.api_auth_access import ApiAuthAccess
from models.event import Event


class AdminApiAuthAdd(LoggedInHandler):
    """
    Create an ApiAuthAccess. POSTs to AdminApiAuthEdit.
    """
    def get(self):
        self._require_admin()

        self.template_values.update({
            "auth_id": ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(16)),
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/api_add_auth.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminApiAuthDelete(LoggedInHandler):
    """
    Delete an ApiAuthAccess.
    """
    def get(self, auth_id):
        self._require_admin()

        auth = ApiAuthAccess.get_by_id(auth_id)

        self.template_values.update({
            "auth": auth
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/api_delete_auth.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, auth_id):
        self._require_admin()

        logging.warning("Deleting auth: %s at the request of %s / %s" % (
            auth_id,
            self.user_bundle.user.user_id(),
            self.user_bundle.user.email()))

        auth = ApiAuthAccess.get_by_id(auth_id)
        auth.key.delete()

        self.redirect("/admin/api_auth/manage")


class AdminApiAuthEdit(LoggedInHandler):
    """
    Edit an ApiAuthAccess.
    """
    def get(self, auth_id):
        self._require_admin()

        auth = ApiAuthAccess.get_by_id(auth_id)
        auth.event_list_str = ','.join([event_key.id() for event_key in auth.event_list])

        self.template_values.update({
            "auth": auth,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/api_edit_auth.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, auth_id):
        self._require_admin()

        auth = ApiAuthAccess.get_by_id(auth_id)

        auth_types_enum = []
        if self.request.get('allow_edit_teams'):
            auth_types_enum.append(AuthType.EVENT_TEAMS)
        if self.request.get('allow_edit_matches'):
            auth_types_enum.append(AuthType.EVENT_MATCHES)
        if self.request.get('allow_edit_rankings'):
            auth_types_enum.append(AuthType.EVENT_RANKINGS)
        if self.request.get('allow_edit_alliances'):
            auth_types_enum.append(AuthType.EVENT_ALLIANCES)
        if self.request.get('allow_edit_awards'):
            auth_types_enum.append(AuthType.EVENT_AWARDS)
        if self.request.get('allow_edit_match_video'):
            auth_types_enum.append(AuthType.MATCH_VIDEO)

        if not auth:
            auth = ApiAuthAccess(
                id=auth_id,
                description=self.request.get('description'),
                secret=''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(64)),
                event_list=[ndb.Key(Event, event_key.strip()) for event_key in self.request.get('event_list_str').split(',')],
                auth_types_enum=auth_types_enum,
            )
        else:
            auth.description = self.request.get('description')
            auth.event_list = event_list=[ndb.Key(Event, event_key.strip()) for event_key in self.request.get('event_list_str').split(',')]
            auth.auth_types_enum = auth_types_enum

        auth.put()

        self.redirect("/admin/api_auth/manage")


class AdminApiAuthManage(LoggedInHandler):
    """
    List all ApiAuthAccesses
    """
    def get(self):
        self._require_admin()

        auths = ApiAuthAccess.query().fetch(None)

        self.template_values.update({
            'auths': auths,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/api_manage_auth.html')
        self.response.out.write(template.render(path, self.template_values))
