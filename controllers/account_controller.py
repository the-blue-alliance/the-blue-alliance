import os
import logging

from google.appengine.ext.webapp import template

from base_controller import LoggedInHandler

from consts.notification_type import NotificationType

from helpers.validation_helper import ValidationHelper

from models.account import Account
from models.favorite import Favorite
from models.subscription import Subscription


class AccountOverview(LoggedInHandler):
    def get(self):
        self._require_login('/account')
        # Redirects to registration page if account not registered
        self._require_registration('/account/register')

        path = os.path.join(os.path.dirname(__file__), '../templates/account_overview.html')
        self.response.out.write(template.render(path, self.template_values))


class AccountEdit(LoggedInHandler):
    def get(self):
        self._require_login('/account/edit')
        self._require_registration('/account/register')

        path = os.path.join(os.path.dirname(__file__), '../templates/account_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/edit')
        self._require_registration('/account/register')

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            user = Account.get_by_id(self.user_bundle.account.key.id())
            user.display_name = self.request.get('display_name')
            user.put()
            self.redirect('/account')
        else:
            self.redirect('/')


class AccountRegister(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        # Redirects to account overview page if already registered
        if self.user_bundle.account.registered:
            self.redirect('/account')
            return None

        path = os.path.join(os.path.dirname(__file__), '../templates/account_register.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/register')
        if self.user_bundle.account.registered:
            self.redirect('/account')
            return None

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            account = Account.get_by_id(self.user_bundle.account.key.id())
            account.display_name = self.request.get('display_name')
            account.registered = True
            account.put()
            self.redirect('/account')
        else:
            self.redirect('/')


class AccountLogout(LoggedInHandler):
    def get(self):
        if os.environ.get('SERVER_SOFTWARE', '').startswith('Development/'):
            self.redirect(self.user_bundle.logout_url)
            return

        # Deletes the session cookies pertinent to TBA without touching Google session(s)
        # Reference: http://ptspts.blogspot.ca/2011/12/how-to-log-out-from-appengine-app-only.html
        response = self.redirect('/')
        response.delete_cookie('ACSID')
        response.delete_cookie('SACSID')

        return response


class MyTBAController(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        user_id = self.user_bundle.account.key.id()
        self.template_values['favorites'] = Favorite.query(Favorite.user_id == user_id).fetch()
        self.template_values['subscriptions'] = Subscription.query(Subscription.user_id == user_id).fetch()
        self.template_values['enabled_notifications'] = NotificationType.enabled_notifications
        path = os.path.join(os.path.dirname(__file__), '../templates/mytba.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        current_user_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if current_user_id == target_account_id:
            action = self.request.get('action')
            if action == "favorite_add":
                model = self.request.get('model_key')
                if not ValidationHelper.is_valid_model_key(model):
                    self.redirect('/account/mytba')
                    return
                favorite = Favorite(model_key =  model, user_id = current_user_id)
                favorite.put()
                # TODO send updated favorite push
                self.redirect('/account/mytba')
                return
            elif action == "favorite_delete":
                client_id = self.request.get('client_id')
                favorite = Favorite.get_by_id(int(client_id))
                if current_user_id == favorite.user_id:
                    favorite.key.delete()
                    # TODO send updated favorites push
                    self.redirect('/account/mytba')
                    return
            elif action == "subscription_add":
                model = self.request.get('model_key')
                if not ValidationHelper.is_valid_model_key(model):
                    self.redirect('/account/mytba')
                    return
                subs = self.request.get_all('notification_types')
                if not subs:
                    # No notification types specified. Don't add
                    self.redirect('/account/mytba')
                    return
                subs = map(int, subs)
                subscription = Subscription(user_id = current_user_id, model_key = model, notification_types = subs)
                subscription.put()
                # TODO send updated subscription push
                self.redirect('/account/mytba')
                return
            elif action == "subscription_delete":
                client_id = self.request.get('client_id')
                subscription = Subscription.get_by_id(int(client_id))
                if current_user_id == subscription.user_id:
                    subscription.key.delete()
                    # TODO send updated subscription push
                    self.redirect('/account/mytba')
                return
        self.redirect('/')
