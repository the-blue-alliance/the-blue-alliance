import os
import logging

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import LoggedInHandler
from consts.client_type import ClientType
from consts.notification_type import NotificationType
from models.mobile_client import MobileClient


class WebhookAdd(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        path = os.path.join(os.path.dirname(__file__), '../templates/webhook_add.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        # Check to make sure that they aren't trying to edit another user
        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if target_account_id == current_user_account_id:
            url = self.request.get('url')
            secret_key = self.request.get('secret')
            query = MobileClient.query(MobileClient.user_id == current_user_account_id, MobileClient.messaging_id == url)
            if query.count() == 0:
                # Webhook doesn't exist, add it
                client = MobileClient( user_id = current_user_account_id, messaging_id = url, secret=secret_key, client_type = ClientType.WEBHOOK)
                client.put()
            else:
                # Webhook already exists. Update the secret
                current = query.fetch()[0]
                current.secret = secret_key
                current.put()
            self.redirect('/account')
        else:
            self.redirect('/')


class WebhookDelete(LoggedInHandler):
    def post(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        # Check to make sure that they aren't trying to edit another user
        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if target_account_id == current_user_account_id:
            to_delete = MobileClient.query(MobileClient.user_id == current_user_account_id, MobileClient.messaging_id == self.request.get('messaging_id').fetch(keys_only=True)
            ndb.delete_multi(to_delete)
            self.redirect('/account')
        else:
            self.redirect('/')
