import os
import logging

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import LoggedInHandler
from consts.client_type import ClientType
from consts.notification_type import NotificationType
from helpers.notification_helper import NotificationHelper
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
                verification_key = NotificationHelper.verify_webhook(url, secret_key)
                logging.info("KEY: "+verification_key)
                client = MobileClient( user_id = current_user_account_id, messaging_id = url, secret=secret_key, client_type = ClientType.WEBHOOK, verified=False, verification_code=verification_key)
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
        client_id = self.request.get('client_id')
        if target_account_id == current_user_account_id:
            to_delete = ndb.Key(MobileClient, int(client_id))
            to_delete.delete()
            self.redirect('/account')
        else:
            self.redirect('/')


class WebhookVerify(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')    
        path = os.path.join(os.path.dirname(__file__), '../templates/webhook_verify.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')


class WebhookVerificationSend(LoggedInHandler):
    def get(self):
        pass
