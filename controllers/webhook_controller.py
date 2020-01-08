import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import LoggedInHandler
from consts.client_type import ClientType
from consts.notification_type import NotificationType
from models.account import Account
from models.mobile_client import MobileClient


class WebhookAdd(LoggedInHandler):
    def get(self):
        self._require_registration()

        self.template_values['error'] = self.request.get('error')

        path = os.path.join(os.path.dirname(__file__), '../templates/webhook_add.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_registration()
        self._require_request_user_is_bundle_user()

        # Name and URL must be non-None
        url = self.request.get('url', None)
        name = self.request.get('name', None)
        if not url or not name:
            return self.redirect('/webhooks/add?error=1')

        # Always generate secret server-side; previously allowed clients to set the secret
        import uuid
        secret = uuid.uuid4().hex

        current_user_account_id = self.user_bundle.account.key.id()
        query = MobileClient.query(MobileClient.messaging_id == url, ancestor=ndb.Key(Account, current_user_account_id))
        if query.count() == 0:
            # Webhook doesn't exist, add it
            from helpers.tbans_helper import TBANSHelper
            verification_key = TBANSHelper.verify_webhook(url, secret)

            client = MobileClient(
                parent=self.user_bundle.account.key,
                user_id=current_user_account_id,
                messaging_id=url,
                display_name=name,
                secret=secret,
                client_type=ClientType.WEBHOOK,
                verified=False,
                verification_code=verification_key)
            client.put()
        else:
            # Webhook already exists. Update the secret
            current = query.fetch()[0]
            current.secret = secret
            current.put()

        self.redirect('/account')


class WebhookDelete(LoggedInHandler):
    def post(self):
        self._require_registration()
        self._require_request_user_is_bundle_user()

        current_user_account_id = self.user_bundle.account.key.id()
        if not current_user_account_id:
            return self.redirect('/')

        client_id = self.request.get('client_id')
        if not client_id:
            return self.redirect('/')

        to_delete = ndb.Key(Account, current_user_account_id, MobileClient, int(client_id))
        to_delete.delete()
        return self.redirect('/account')


class WebhookVerify(LoggedInHandler):
    def get(self, client_id):
        self._require_registration()

        self.template_values['client_id'] = client_id
        self.template_values['error'] = self.request.get('error')

        path = os.path.join(os.path.dirname(__file__), '../templates/webhook_verify.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, client_id):
        self._require_registration()
        self._require_request_user_is_bundle_user()

        current_user_account_id = self.user_bundle.account.key.id()
        if not current_user_account_id:
            return self.redirect('/')

        verification = self.request.get('code')
        if not verification:
            return self.redirect('/webhooks/verify/{}?error=1'.format(webhook.key.id()))

        webhook = MobileClient.get_by_id(int(client_id), parent=ndb.Key(Account, current_user_account_id))
        if not webhook or webhook.client_type != ClientType.WEBHOOK or current_user_account_id != webhook.user_id:
            return self.redirect('/')

        if verification == webhook.verification_code:
            webhook.verified = True
            webhook.put()
            return self.redirect('/account?webhook_verification_success=1')
        else:
            # Redirect back to the verification page
            return self.redirect('/webhooks/verify/{}?error=1'.format(webhook.key.id()))


class WebhookVerificationSend(LoggedInHandler):
    def post(self):
        self._require_registration()
        self._require_request_user_is_bundle_user()

        current_user_account_id = self.user_bundle.account.key.id()
        if not current_user_account_id:
            return self.redirect('/')

        client_id = self.request.get('client_id')
        if not client_id:
            return self.redirect('/')

        webhook = MobileClient.get_by_id(int(client_id), parent=ndb.Key(Account, current_user_account_id))
        if not webhook or webhook.client_type != ClientType.WEBHOOK or current_user_account_id != webhook.user_id:
            return self.redirect('/')

        from helpers.tbans_helper import TBANSHelper
        verification_key = TBANSHelper.verify_webhook(webhook.messaging_id, webhook.secret)

        webhook.verification_code = verification_key
        webhook.verified = False
        webhook.put()

        return self.redirect('/account')
