import json
import logging
import random
import string
import os
from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.auth_type import AuthType
from controllers.base_controller import LoggedInHandler
from models.account import Account
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

        auth_types_enum = [AuthType.READ_API] if auth and AuthType.READ_API in auth.auth_types_enum else []
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
        if self.request.get('allow_edit_info'):
            auth_types_enum.append(AuthType.EVENT_INFO)
        if self.request.get('allow_edit_zebra_motionworks'):
            auth_types_enum.append(AuthType.ZEBRA_MOTIONWORKS)

        if self.request.get('owner', None):
            owner = Account.query(Account.email == self.request.get('owner')).fetch()
            owner_key = owner[0].key if owner else None
        else:
            owner_key = None

        if self.request.get('expiration', None):
            expiration = datetime.strptime(self.request.get('expiration'), '%Y-%m-%d')
        else:
            expiration = None

        if self.request.get('event_list_str'):
            split_events = self.request.get('event_list_str', '').split(',')
            event_list = [ndb.Key(Event, event_key.strip()) for event_key in split_events]
        else:
            event_list = []

        if not auth:
            auth = ApiAuthAccess(
                id=auth_id,
                description=self.request.get('description'),
                owner=owner_key,
                expiration=expiration,
                allow_admin=True if self.request.get('allow_admin') else False,
                secret=''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(64)),
                event_list=event_list,
                auth_types_enum=auth_types_enum,
            )
        else:
            auth.description = self.request.get('description')
            auth.event_list = event_list
            auth.auth_types_enum = auth_types_enum
            auth.owner = owner_key
            auth.expiration = expiration
            auth.allow_admin = True if self.request.get('allow_admin') else False

        auth.put()

        self.redirect("/admin/api_auth/manage")


class AdminApiAuthManage(LoggedInHandler):
    """
    List all ApiAuthAccesses
    """
    def get(self):
        self._require_admin()

        auths = ApiAuthAccess.query().fetch()
        write_auths = filter(lambda auth: auth.is_write_key, auths)
        read_auths = filter(lambda auth: auth.is_read_key, auths)
        admin_auths = filter(lambda auth: auth.allow_admin, auths)

        self.template_values.update({
            'write_auths': write_auths,
            'read_auths': read_auths,
            'admin_auths': admin_auths,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/api_manage_auth.html')
        self.response.out.write(template.render(path, self.template_values))
