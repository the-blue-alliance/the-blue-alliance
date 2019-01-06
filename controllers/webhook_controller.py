import os
import logging

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import LoggedInHandler
from consts.client_type import ClientType
from consts.notification_type import NotificationType
from helpers.tbans_helper import TBANSHelper
from models.account import Account
from models.mobile_client import MobileClient


class WebhookAdd(LoggedInHandler):
    def get(self):
        self._require_registration()

        path = os.path.join(os.path.dirname(__file__), '../templates/webhook_add.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_registration()

        # Check to make sure that they aren't trying to edit another user
        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if target_account_id == current_user_account_id:
            url = self.request.get('url')
            secret_key = self.request.get('secret')
            query = MobileClient.query(MobileClient.messaging_id == url, ancestor=ndb.Key(Account, current_user_account_id))
            if query.count() == 0:
                # Webhook doesn't exist, add it
                response = TBANSHelper.verify_webhook(url, secret_key)
                client = MobileClient(
                    parent=self.user_bundle.account.key,
                    user_id=current_user_account_id,
                    messaging_id=url,
                    display_name = self.request.get('name'),
                    secret=secret_key,
                    client_type=ClientType.WEBHOOK,
                    verified=False,
                    verification_code=response.verification_key)
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
        self._require_registration()

        # Check to make sure that they aren't trying to edit another user
        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        client_id = self.request.get('client_id')
        if target_account_id == current_user_account_id:
            to_delete = ndb.Key(Account, current_user_account_id, MobileClient, int(client_id))
            to_delete.delete()
            self.redirect('/account')
        else:
            self.redirect('/')


class WebhookVerify(LoggedInHandler):
    def get(self, client_id):
        self._require_registration()

        self.template_values['client_id'] = client_id
        self.template_values['error'] = self.request.get('error')

        path = os.path.join(os.path.dirname(__file__), '../templates/webhook_verify.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, client_id):
        self._require_registration()

        # Check to make sure the user isn't trying to impersonate another
        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if target_account_id == current_user_account_id:
            verification = self.request.get('code')
            webhook = MobileClient.get_by_id(int(client_id), parent=ndb.Key(Account, current_user_account_id))
            if webhook.client_type == ClientType.WEBHOOK and current_user_account_id == webhook.user_id:
                if verification == webhook.verification_code:
                    logging.info("webhook verified")
                    webhook.verified = True
                    webhook.put()
                    self.redirect('/account?webhook_verification_success=1')
                    return
                else:  # Verification failed
                    # Redirect back to the verification page
                    self.redirect('/webhooks/verify/{}?error=1'.format(webhook.key.id()))
                    return
        self.redirect('/')


class WebhookVerificationSend(LoggedInHandler):
    def post(self):
        self._require_registration()

        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if target_account_id == current_user_account_id:
            client_id = self.request.get('client_id')
            webhook = MobileClient.get_by_id(int(client_id), parent=ndb.Key(Account, current_user_account_id))
            if webhook.client_type == ClientType.WEBHOOK and current_user_account_id == webhook.user_id:
                response = TBANSHelper.verify_webhook(webhook.messaging_id, webhook.secret)
                webhook.verification_code = response.verification_key
                webhook.verified = False
                webhook.put()
                self.redirect('/account')
                return
            else:
                logging.warning("Not webhook, or wrong owner")
        else:
            logging.warning("Users don't match. "+current_user_account_id+"/"+target_account_id)
        self.redirect('/')
